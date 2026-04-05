import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import DocumentList from "./DocumentList";

const mockDocs = [
  { id: "1", filename: "report.pdf", chunks: 5, characters: 3200 },
  { id: "2", filename: "data.csv", chunks: 3, characters: 1800 },
  { id: "3", filename: "notes.md", chunks: 2, characters: 950 },
];

describe("DocumentList", () => {
  it("renders nothing when no documents", () => {
    const { container } = render(
      <DocumentList documents={[]} activeDocId={null} onSelect={() => {}} onDelete={() => {}} />
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders all documents", () => {
    render(
      <DocumentList documents={mockDocs} activeDocId={null} onSelect={() => {}} onDelete={() => {}} />
    );
    expect(screen.getByText("report.pdf")).toBeInTheDocument();
    expect(screen.getByText("data.csv")).toBeInTheDocument();
    expect(screen.getByText("notes.md")).toBeInTheDocument();
  });

  it("shows file type badges", () => {
    render(
      <DocumentList documents={mockDocs} activeDocId={null} onSelect={() => {}} onDelete={() => {}} />
    );
    expect(screen.getByText("pdf")).toBeInTheDocument();
    expect(screen.getByText("csv")).toBeInTheDocument();
    expect(screen.getByText("md")).toBeInTheDocument();
  });

  it("shows chunk and character counts", () => {
    render(
      <DocumentList documents={[mockDocs[0]]} activeDocId={null} onSelect={() => {}} onDelete={() => {}} />
    );
    expect(screen.getByText("5 chunks")).toBeInTheDocument();
    expect(screen.getByText("3.2k chars")).toBeInTheDocument();
  });

  it("highlights the active document", () => {
    render(
      <DocumentList documents={mockDocs} activeDocId="2" onSelect={() => {}} onDelete={() => {}} />
    );
    const activeItem = screen.getByText("data.csv").closest(".doc-item");
    expect(activeItem).toHaveClass("active");
  });

  it("calls onSelect when clicking a document", () => {
    const onSelect = vi.fn();
    render(
      <DocumentList documents={mockDocs} activeDocId={null} onSelect={onSelect} onDelete={() => {}} />
    );
    fireEvent.click(screen.getByText("report.pdf"));
    expect(onSelect).toHaveBeenCalledWith("1");
  });

  it("calls onDelete when clicking delete button", () => {
    const onDelete = vi.fn();
    render(
      <DocumentList documents={mockDocs} activeDocId={null} onSelect={() => {}} onDelete={onDelete} />
    );
    const deleteButtons = screen.getAllByTitle("Delete document");
    fireEvent.click(deleteButtons[0]);
    expect(onDelete).toHaveBeenCalledWith("1");
  });

  it("does not trigger onSelect when deleting", () => {
    const onSelect = vi.fn();
    const onDelete = vi.fn();
    render(
      <DocumentList documents={mockDocs} activeDocId={null} onSelect={onSelect} onDelete={onDelete} />
    );
    const deleteButtons = screen.getAllByTitle("Delete document");
    fireEvent.click(deleteButtons[1]);
    expect(onDelete).toHaveBeenCalledWith("2");
    expect(onSelect).not.toHaveBeenCalled();
  });
});
