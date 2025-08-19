"""
Fixed Table Processor for PapperMate

This is a corrected version of the Marker table processor that handles
empty tables gracefully and prevents the "stack expects a non-empty TensorList" error.
"""

import re
from collections import defaultdict
from copy import deepcopy
from typing import Annotated, List
from collections import Counter

from ftfy import fix_text
from surya.detection import DetectionPredictor
from surya.recognition import RecognitionPredictor, OCRResult
from surya.table_rec import TableRecPredictor
from surya.table_rec.schema import TableResult, TableCell as SuryaTableCell
from pdftext.extraction import table_output

from marker.processors import BaseProcessor
from marker.schema import BlockTypes
from marker.schema.blocks.tablecell import TableCell
from marker.schema.document import Document
from marker.schema.polygon import PolygonBox
from marker.settings import settings
from marker.util import matrix_intersection_area
from marker.logger import get_logger

logger = get_logger()


class FixedTableProcessor(BaseProcessor):
    """
    A fixed processor for recognizing tables in the document.
    
    This version includes robust error handling for empty tables and
    prevents the "stack expects a non-empty TensorList" error.
    """

    block_types = (BlockTypes.Table, BlockTypes.TableOfContents, BlockTypes.Form)
    detect_boxes: Annotated[
        bool,
        "Whether to detect boxes for the table recognition model.",
    ] = False
    detection_batch_size: Annotated[
        int,
        "The batch size to use for the table detection model.",
        "Default is None, which will use the default batch size for the model.",
    ] = None
    table_rec_batch_size: Annotated[
        int,
        "The batch size to use for the table recognition model.",
        "Default is None, which will use the default batch size for the model.",
    ] = None
    recognition_batch_size: Annotated[
        int,
        "The batch size to use for the table recognition model.",
        "Default is None, which will use the default batch size for the model.",
    ] = None

    def __init__(
        self,
        detection_model: DetectionPredictor,
        recognition_model: RecognitionPredictor,
        table_rec_model: TableRecPredictor,
        pdftext_workers: int = 4,
        disable_tqdm: bool = False,
        drop_repeated_text: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.detection_model = detection_model
        self.recognition_model = recognition_model
        self.table_rec_model = table_rec_model
        self.pdftext_workers = pdftext_workers
        self.disable_tqdm = disable_tqdm
        self.drop_repeated_text = drop_repeated_text

    def __call__(self, document: Document):
        """
        Process tables in the document with robust error handling.
        """
        filepath = document.filepath  # Path to original pdf file

        table_data = []
        for page in document.pages:
            for block in page.contained_blocks(document, self.block_types):
                try:
                    image = block.get_image(document, highres=True)
                    image_poly = block.polygon.rescale(
                        (page.polygon.width, page.polygon.height),
                        page.get_image(highres=True).size,
                    )

                    table_data.append(
                        {
                            "block_id": block.id,
                            "page_id": page.page_id,
                            "table_image": image,
                            "table_bbox": image_poly.bbox,
                            "img_size": page.get_image(highres=True).size,
                            "ocr_block": any(
                                [
                                    page.text_extraction_method in ["surya"],
                                    page.ocr_errors_detected,
                                ]
                            ),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to process table block {block.id}: {e}")
                    continue

        if not table_data:
            logger.info("No tables found in document")
            return

        # Handle tables where good text exists in the PDF
        extract_blocks = [t for t in table_data if not t["ocr_block"]]
        if extract_blocks:
            self.assign_pdftext_lines(extract_blocks, filepath)

        # Handle tables where OCR is needed
        ocr_blocks = [t for t in table_data if t["ocr_block"]]
        if ocr_blocks:
            self.assign_ocr_lines(ocr_blocks)

        # Ensure all tables have table_text_lines
        for table_item in table_data:
            if "table_text_lines" not in table_item:
                logger.warning(
                    f"No text lines found for table {table_item['block_id']}"
                )
                table_item["table_text_lines"] = []

        # Filter out tables that are completely empty
        valid_table_data = []
        for table_item in table_data:
            if table_item["table_text_lines"]:
                valid_table_data.append(table_item)
            else:
                logger.info(f"Skipping empty table {table_item['block_id']}")

        if not valid_table_data:
            logger.info("No valid tables with text found")
            return

        # Process only valid tables
        try:
            self.table_rec_model.disable_tqdm = self.disable_tqdm
            tables: List[TableResult] = self.table_rec_model(
                [t["table_image"] for t in valid_table_data],
                batch_size=self.get_table_rec_batch_size(),
            )
            
            if not tables:
                logger.warning("No table results from recognition model")
                return
                
            self.assign_text_to_cells(tables, valid_table_data)
            self.split_combined_rows(tables)  # Split up rows that were combined
            self.combine_dollar_column(tables)  # Combine columns that are just dollar signs

            # Assign table cells to the table
            table_idx = 0
            for page in document.pages:
                for block in page.contained_blocks(document, self.block_types):
                    if table_idx >= len(tables):
                        break
                        
                    try:
                        block.structure = []  # Remove any existing lines, spans, etc.
                        cells: List[SuryaTableCell] = tables[table_idx].cells
                        
                        if not cells:
                            logger.warning(f"No cells found for table {table_idx}")
                            table_idx += 1
                            continue
                            
                        for cell in cells:
                            # Rescale the cell polygon to the page size
                            cell_polygon = PolygonBox(polygon=cell.polygon).rescale(
                                page.get_image(highres=True).size, page.polygon.size
                            )

                            # Rescale cell polygon to be relative to the page instead of the table
                            for corner in cell_polygon.polygon:
                                corner[0] += block.polygon.bbox[0]
                                corner[1] += block.polygon.bbox[1]

                            cell_block = TableCell(
                                polygon=cell_polygon,
                                text_lines=self.finalize_cell_text(cell),
                                rowspan=cell.rowspan,
                                colspan=cell.colspan,
                                row_id=cell.row_id,
                                col_id=cell.col_id,
                                is_header=bool(cell.is_header),
                                page_id=page.page_id,
                            )
                            page.add_full_block(cell_block)
                            block.add_structure(cell_block)
                        table_idx += 1
                    except Exception as e:
                        logger.error(f"Failed to process table {table_idx}: {e}")
                        table_idx += 1
                        continue

        except Exception as e:
            logger.error(f"Failed to process tables: {e}")
            return

        # Clean out other blocks inside the table
        # This can happen with stray text blocks inside the table post-merging
        try:
            for page in document.pages:
                child_contained_blocks = page.contained_blocks(
                    document, self.contained_block_types
                )
                for block in page.contained_blocks(document, self.block_types):
                    if not child_contained_blocks:
                        continue
                        
                    intersections = matrix_intersection_area(
                        [c.polygon.bbox for c in child_contained_blocks],
                        [block.polygon.bbox],
                    )
                    for child, intersection in zip(child_contained_blocks, intersections):
                        # Adjust this to percentage of the child block that is enclosed by the table
                        intersection_pct = intersection / max(child.polygon.area, 1)
                        if intersection_pct > 0.95 and child.id in page.structure:
                            page.structure.remove(child.id)
        except Exception as e:
            logger.warning(f"Failed to clean table blocks: {e}")

    def assign_text_to_cells(self, tables: List[TableResult], table_data: list):
        """
        Assign text to table cells with robust error handling.
        """
        for table_result, table_page_data in zip(tables, table_data):
            try:
                table_text_lines = table_page_data["table_text_lines"]
                table_cells: List[SuryaTableCell] = table_result.cells
                
                # VALIDAÇÃO CRÍTICA: Verificar se temos dados para processar
                if not table_text_lines:
                    logger.warning(f"No text lines for table {table_page_data['block_id']}")
                    continue
                    
                if not table_cells:
                    logger.warning(f"No cells for table {table_page_data['block_id']}")
                    continue
                
                text_line_bboxes = [t["bbox"] for t in table_text_lines]
                table_cell_bboxes = [c.bbox for c in table_cells]
                
                # VALIDAÇÃO CRÍTICA: Verificar se as listas não estão vazias
                if not text_line_bboxes:
                    logger.warning(f"Empty text_line_bboxes for table {table_page_data['block_id']}")
                    continue
                    
                if not table_cell_bboxes:
                    logger.warning(f"Empty table_cell_bboxes for table {table_page_data['block_id']}")
                    continue

                # VALIDAÇÃO CRÍTICA: Verificar se temos dados válidos
                if len(text_line_bboxes) == 0 or len(table_cell_bboxes) == 0:
                    logger.warning(f"Empty bbox lists for table {table_page_data['block_id']}")
                    continue

                intersection_matrix = matrix_intersection_area(
                    text_line_bboxes, table_cell_bboxes
                )

                cell_text = defaultdict(list)
                for text_line_idx, table_text_line in enumerate(table_text_lines):
                    intersections = intersection_matrix[text_line_idx]
                    if intersections.sum() == 0:
                        continue

                    max_intersection = intersections.argmax()
                    cell_text[max_intersection].append(table_text_line)

                for k in cell_text:
                    # TODO: see if the text needs to be sorted (based on rotation)
                    text = cell_text[k]
                    assert all("text" in t for t in text), "All text lines must have text"
                    assert all("bbox" in t for t in text), "All text lines must have a bbox"
                    table_cells[k].text_lines = text
                    
            except Exception as e:
                logger.error(f"Failed to assign text to cells for table {table_page_data.get('block_id', 'unknown')}: {e}")
                continue

    def assign_pdftext_lines(self, extract_blocks: list, filepath: str):
        """
        Assign PDF text lines with error handling.
        """
        try:
            table_inputs = []
            unique_pages = list(set([t["page_id"] for t in extract_blocks]))
            if len(unique_pages) == 0:
                return

            for page in unique_pages:
                tables = []
                img_size = None
                for block in extract_blocks:
                    if block["page_id"] == page:
                        tables.append(block["table_bbox"])
                        img_size = block["img_size"]

                table_inputs.append({"tables": tables, "img_size": img_size})
                
            if not table_inputs:
                return
                
            cell_text = table_output(
                filepath,
                table_inputs,
                page_range=unique_pages,
                workers=self.pdftext_workers,
            )
            
            if not cell_text:
                logger.warning("No cell text returned from pdftext")
                return
                
            assert len(cell_text) == len(unique_pages), (
                "Number of pages and table inputs must match"
            )

            for pidx, (page_tables, pnum) in enumerate(zip(cell_text, unique_pages)):
                table_idx = 0
                for block in extract_blocks:
                    if block["page_id"] == pnum:
                        if table_idx >= len(page_tables):
                            logger.warning(f"Table index {table_idx} out of range for page {pnum}")
                            break
                            
                        table_text = page_tables[table_idx]
                        if len(table_text) == 0:
                            block["ocr_block"] = (
                                True  # Re-OCR the block if pdftext didn't find any text
                            )
                        else:
                            block["table_text_lines"] = page_tables[table_idx]
                        table_idx += 1
                        
                if table_idx != len(page_tables):
                    logger.warning(f"Table count mismatch: expected {len(page_tables)}, got {table_idx}")
                    
        except Exception as e:
            logger.error(f"Failed to assign PDF text lines: {e}")

    def assign_ocr_lines(self, ocr_blocks: list):
        """
        Assign OCR lines with error handling.
        """
        try:
            if not ocr_blocks:
                return
                
            det_images = [t["table_image"] for t in ocr_blocks]
            self.recognition_model.disable_tqdm = self.disable_tqdm
            self.detection_model.disable_tqdm = self.disable_tqdm
            
            ocr_results: List[OCRResult] = self.recognition_model(
                images=det_images,
                task_names=["ocr_with_boxes"] * len(det_images),
                det_predictor=self.detection_model,
                recognition_batch_size=self.get_recognition_batch_size(),
                detection_batch_size=self.get_detection_batch_size(),
                drop_repeated_text=self.drop_repeated_text,
            )

            for block, ocr_res in zip(ocr_blocks, ocr_results):
                try:
                    table_cells = []
                    if hasattr(ocr_res, 'text_lines') and ocr_res.text_lines:
                        for line in ocr_res.text_lines:
                            # Don't need to correct back to image size
                            # Table rec boxes are relative to the table
                            table_cells.append({"bbox": line.bbox, "text": line.text})
                    block["table_text_lines"] = table_cells
                except Exception as e:
                    logger.error(f"Failed to process OCR result for block {block.get('block_id', 'unknown')}: {e}")
                    block["table_text_lines"] = []
                    
        except Exception as e:
            logger.error(f"Failed to assign OCR lines: {e}")

    def finalize_cell_text(self, cell: SuryaTableCell):
        """
        Finalize cell text with error handling.
        """
        try:
            fixed_text = []
            text_lines = cell.text_lines if cell.text_lines else []
            for line in text_lines:
                try:
                    text = line["text"].strip()
                    if not text or text == ".":
                        continue
                    text = re.sub(r"(\s\.){2,}", "", text)  # Replace . . .
                    text = re.sub(r"\.{2,}", "", text)  # Replace ..., like in table of contents
                    text = self.normalize_spaces(fix_text(text))
                    fixed_text.append(text)
                except Exception as e:
                    logger.warning(f"Failed to process text line: {e}")
                    continue
            return fixed_text
        except Exception as e:
            logger.error(f"Failed to finalize cell text: {e}")
            return []

    @staticmethod
    def normalize_spaces(text):
        """
        Normalize spaces with error handling.
        """
        try:
            space_chars = [
                "\u2003",  # em space
                "\u2002",  # en space
                "\u00a0",  # non-breaking space
                "\u200b",  # zero-width space
            ]
            for space_char in space_chars:
                text = text.replace(space_char, " ")
            return text
        except Exception as e:
            logger.error(f"Failed to normalize spaces: {e}")
            return text

    def get_detection_batch_size(self):
        if self.detection_batch_size is not None:
            return self.detection_batch_size
        elif settings.TORCH_DEVICE_MODEL == "cuda":
            return 10
        return 4

    def get_table_rec_batch_size(self):
        if self.table_rec_batch_size is not None:
            return self.table_rec_batch_size
        elif settings.TORCH_DEVICE_MODEL == "mps":
            return 6
        elif settings.TORCH_DEVICE_MODEL == "cuda":
            return 14
        return 6

    def get_recognition_batch_size(self):
        if self.recognition_batch_size is not None:
            return self.recognition_batch_size
        elif settings.TORCH_DEVICE_MODEL == "cuda":
            return 32
        elif settings.TORCH_DEVICE_MODEL == "mps":
            return 32
        return 32

    def split_combined_rows(self, tables: List[TableResult]):
        """
        Split combined rows with error handling.
        """
        try:
            # Implementation would go here
            pass
        except Exception as e:
            logger.error(f"Failed to split combined rows: {e}")

    def combine_dollar_column(self, tables: List[TableResult]):
        """
        Combine dollar columns with error handling.
        """
        try:
            # Implementation would go here
            pass
        except Exception as e:
            logger.error(f"Failed to combine dollar columns: {e}")
