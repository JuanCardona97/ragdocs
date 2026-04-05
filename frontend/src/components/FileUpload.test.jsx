import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import FileUpload from "./FileUpload";

describe("FileUpload", () => {
  it("renders the dropzone", () => {
    render(<FileUpload apiUrl="http://localhost:8000" onUpload={() => {}} />);
    expect(screen.getByText(/drop a file here/i)).toBeInTheDocument();
  });

  it("shows supported file formats", () => {
    render(<FileUpload apiUrl="http://localhost:8000" onUpload={() => {}} />);
    expect(screen.getByText(/PDF, DOCX, TXT, MD, CSV, XLSX/i)).toBeInTheDocument();
  });

  it("shows processing state during upload", async () => {
    // Mock a slow fetch
    global.fetch = vi.fn(() => new Promise(() => {}));

    render(<FileUpload apiUrl="http://localhost:8000" onUpload={() => {}} />);

    const input = document.querySelector('input[type="file"]');
    const file = new File(["test content"], "test.txt", { type: "text/plain" });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/processing document/i)).toBeInTheDocument();
    });
  });

  it("calls onUpload after successful upload", async () => {
    const mockDoc = { id: "123", filename: "test.txt", chunks: 2, characters: 100 };
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ document: mockDoc }),
      })
    );

    const onUpload = vi.fn();
    render(<FileUpload apiUrl="http://localhost:8000" onUpload={onUpload} />);

    const input = document.querySelector('input[type="file"]');
    const file = new File(["test content"], "test.txt", { type: "text/plain" });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(onUpload).toHaveBeenCalledWith(mockDoc);
    });
  });

  it("shows error on upload failure", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ detail: "File too large" }),
      })
    );

    render(<FileUpload apiUrl="http://localhost:8000" onUpload={() => {}} />);

    const input = document.querySelector('input[type="file"]');
    const file = new File(["x".repeat(100)], "big.pdf", { type: "application/pdf" });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("File too large")).toBeInTheDocument();
    });
  });

  it("applies active class on drag over", () => {
    render(<FileUpload apiUrl="http://localhost:8000" onUpload={() => {}} />);
    const dropzone = document.querySelector(".dropzone");

    fireEvent.dragOver(dropzone, { preventDefault: () => {} });
    expect(dropzone).toHaveClass("active");
  });
});
