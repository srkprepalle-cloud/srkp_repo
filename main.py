from calculate import divison, sub
from pdf_reader import read_pdf


def main():
    pdf_text = ""
    pdf_text = read_pdf("files/Java-for-Dummies.pdf")    
    print(f"Text from pdf : {pdf_text}")


if __name__ == "__main__":
    main()