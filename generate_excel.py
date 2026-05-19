import os
import re
from datetime import datetime
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_EXCEL = os.path.join(BASE_DIR, "scraped_results", "sikkim_policy_files_index.xlsx")
PDF_DIR = os.path.join(BASE_DIR, "sikkim_policy_briefs")

def get_file_size_display(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"

def main():
    print("=========================================================")
    print("Generating Professional Excel File for Sikkim Policy Briefs")
    print("=========================================================")

    if not os.path.exists(PDF_DIR):
        print(f"Error: Policy briefs directory not found at {PDF_DIR}")
        return

    # Scan the hierarchical structure under sikkim_policy_briefs
    local_rows = []
    local_idx = 1

    # Walk through the subdirectories in sikkim_policy_briefs
    for root, dirs, files in os.walk(PDF_DIR):
        # Sort files to keep output ordered
        for file in sorted(files):
            if not file.lower().endswith(".pdf"):
                continue  # Only index the policy brief PDF files
                
            file_path = os.path.join(root, file)
            # Get path relative to the sikkim_policy_briefs folder
            rel_path = os.path.relpath(file_path, PDF_DIR)
            name, ext = os.path.splitext(file)
            size_bytes = os.path.getsize(file_path)
            mtime = os.path.getmtime(file_path)
            modified_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            # The category is the immediate subfolder name
            category = os.path.basename(root)
            if category == "sikkim_policy_briefs":
                category = "General"  # Fallback if file is in root

            # Beautify category name for display
            display_category = category.replace("_", " ")

            local_rows.append({
                "S.No": local_idx,
                "Relative Path": f"sikkim_policy_briefs/{rel_path.replace('\\', '/')}",
                "Name": name,
                "Item Type": "PDF Policy Brief",
                "Extension": ext,
                "Size": get_file_size_display(size_bytes),
                "Modified": modified_str,
                "Category": display_category
            })
            local_idx += 1

    if not local_rows:
        print("Warning: No policy PDFs found to index.")
        df_local = pd.DataFrame(columns=["S.No", "Relative Path", "Name", "Item Type", "Extension", "Size", "Modified", "Category"])
    else:
        df_local = pd.DataFrame(local_rows)

    # Make output directory if needed
    os.makedirs(os.path.dirname(OUTPUT_EXCEL), exist_ok=True)

    # Write to Excel
    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        df_local.to_excel(writer, sheet_name="Policy Briefs Index", index=False)

    # Re-open the file with openpyxl to apply premium styles
    wb = openpyxl.load_workbook(OUTPUT_EXCEL)

    # Styling Elements
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid") # Dark Teal/Blue
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=10, color="000000")
    sno_font = Font(name="Segoe UI", size=10, bold=True, color="555555")

    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    zebra_fill = PatternFill(start_color="F2F6FA", end_color="F2F6FA", fill_type="solid") # Very light blue tint
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]

        # Enable grid lines explicitly
        ws.views.sheetView[0].showGridLines = True

        # Header height and styling
        ws.row_dimensions[1].height = 28

        # Format Headers
        for col_idx in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border

        # Format Data Rows
        for row_idx in range(2, ws.max_row + 1):
            ws.row_dimensions[row_idx].height = 20
            is_even = (row_idx % 2 == 0)
            current_fill = zebra_fill if is_even else white_fill

            for col_idx in range(1, ws.max_column + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.fill = current_fill
                cell.border = thin_border
                
                # Check column headers
                header_name = ws.cell(row=1, column=col_idx).value

                # Default alignments & fonts
                if header_name == "S.No":
                    cell.font = sno_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif header_name in ["Extension", "Size", "Modified"]:
                    cell.font = data_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.font = data_font
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        # Auto-fit Column Widths with padding
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                val_len = len(val_str)
                if val_len > max_len:
                    max_len = val_len
            
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(OUTPUT_EXCEL)
    print(f"Success! Excel sheet created and styled at: {OUTPUT_EXCEL}")

if __name__ == "__main__":
    main()
