from .pdf_splitter import sha256_of, split_pdf

pdf_path = "1984.pdf"
batch_dir = f"data/batches/{sha256_of(pdf_path)}"

b = split_pdf(pdf_path, batch_dir)
print(len(b), b[0], b[-1])