from pypdf import PdfReader

def read_pdf(pdfName):
    # Load the PDF file
    reader = PdfReader(pdfName)
    #print(len(reader.pages))
    # Extract text from each page
    full_text = ""
    index = 0
    for pg in reader.pages:
        index = index + 1
        if index > 57 and index < 60:
            full_text += pg.extract_text() + "\n"


    return full_text
