from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

app = FastAPI(title="Smart Library Management API", version="1.0")

# -------------------- DATABASE --------------------
books = []
transactions = []

# -------------------- MODELS --------------------

class Book(BaseModel):
    id: int
    title: str = Field(..., min_length=2)
    author: str
    price: float = Field(..., gt=0)
    available: bool = True

class BorrowRequest(BaseModel):
    user: str = Field(..., min_length=2)
    book_id: int

# -------------------- HELPER FUNCTIONS --------------------

def find_book(book_id: int):
    for book in books:
        if book["id"] == book_id:
            return book
    return None

def format_response(data=None, message="Success"):
    return {
        "timestamp": datetime.now(),
        "message": message,
        "data": data
    }

def apply_filters(keyword: Optional[str], available: Optional[bool]):
    result = books

    if keyword:
        result = [b for b in result if keyword.lower() in b["title"].lower()]

    if available is not None:
        result = [b for b in result if b["available"] == available]

    return result

def apply_pagination(data, page: int, limit: int):
    start = (page - 1) * limit
    end = start + limit
    return data[start:end]

# -------------------- ROOT --------------------

@app.get("/")
def home():
    return format_response(message="🚀 Smart Library API Running")

# -------------------- CRUD OPERATIONS --------------------

@app.post("/books", status_code=status.HTTP_201_CREATED)
def add_book(book: Book):
    if find_book(book.id):
        raise HTTPException(status_code=400, detail="Book ID already exists")

    books.append(book.dict())
    return format_response(book, "Book added successfully")

@app.get("/books")
def get_all_books():
    return format_response(books)

@app.get("/books/count")
def get_book_count():
    return format_response({"total_books": len(books)})

@app.get("/books/{id}")
def get_book_by_id(id: int):
    book = find_book(id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return format_response(book)

@app.put("/books/{id}")
def update_book(id: int, updated_book: Book):
    book = find_book(id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.update(updated_book.dict())
    return format_response(book, "Book updated successfully")

@app.delete("/books/{id}")
def delete_book(id: int):
    book = find_book(id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    books.remove(book)
    return format_response(message="Book deleted successfully")

# -------------------- MULTI-STEP WORKFLOW --------------------

@app.post("/borrow")
def borrow_book(request: BorrowRequest):
    book = find_book(request.book_id)

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book["available"]:
        raise HTTPException(status_code=400, detail="Book already borrowed")

    book["available"] = False

    transactions.append({
        "user": request.user,
        "book_id": request.book_id,
        "borrowed_at": datetime.now(),
        "returned_at": None
    })

    return format_response(message="Book borrowed successfully")

@app.post("/return")
def return_book(request: BorrowRequest):
    book = find_book(request.book_id)

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    for record in transactions:
        if (
            record["book_id"] == request.book_id and
            record["user"] == request.user and
            record["returned_at"] is None
        ):
            record["returned_at"] = datetime.now()
            book["available"] = True
            return format_response(message="Book returned successfully")

    raise HTTPException(status_code=404, detail="Borrow record not found")

@app.get("/transactions")
def get_all_transactions():
    return format_response(transactions)

# -------------------- ADVANCED APIs --------------------

@app.get("/books/search")
def search_books(
    keyword: Optional[str] = Query(None),
    available: Optional[bool] = Query(None)
):
    result = apply_filters(keyword, available)
    return format_response(result)

@app.get("/books/sort")
def sort_books(order: str = "asc"):
    sorted_books = sorted(
        books,
        key=lambda x: x["price"],
        reverse=(order == "desc")
    )
    return format_response(sorted_books)

@app.get("/books/paginate")
def paginate_books(page: int = 1, limit: int = 5):
    return format_response(apply_pagination(books, page, limit))

@app.get("/books/browse")
def browse_books(
    keyword: Optional[str] = None,
    available: Optional[bool] = None,
    order: str = "asc",
    page: int = 1,
    limit: int = 5
):
    data = apply_filters(keyword, available)
    data = sorted(data, key=lambda x: x["price"], reverse=(order == "desc"))
    data = apply_pagination(data, page, limit)

    return format_response(data, "Filtered + Sorted + Paginated results")