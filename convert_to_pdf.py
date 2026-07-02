"""Convert PPTX to PDF on Windows using PowerPoint COM automation."""
import sys
import os

def convert_to_pdf(pptx_path, pdf_path):
    try:
        import win32com.client
    except ImportError:
        print("pywin32 not installed.")
        sys.exit(1)

    powerpoint = win32com.client.Dispatch("Powerpoint.Application")
    try:
        # 32 is the constant for saving as PDF in PowerPoint
        presentation = powerpoint.Presentations.Open(os.path.abspath(pptx_path), WithWindow=False)
        presentation.SaveAs(os.path.abspath(pdf_path), 32)
        presentation.Close()
        print(f"Successfully converted {pptx_path} to {pdf_path}")
    except Exception as e:
        print(f"Failed to convert to PDF: {e}")
    finally:
        powerpoint.Quit()

if __name__ == "__main__":
    convert_to_pdf("Redrob_AI_Approach.pptx", "Redrob_AI_Approach.pdf")
