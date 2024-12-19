from fastapi import FastAPI
from pydantic import ValidationError
from fastapi.responses import FileResponse
from starlette.responses import  JSONResponse
from starlette.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers.product import router as product
from routers.user import router as user



app = FastAPI()
app.include_router(product)

app.include_router(user)
origins = [
    "http://127.0.0.1:8000"
    "http://127.0.0.1:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount('/static', StaticFiles(directory='static'), 'static')


@app.get("/")
async def root():
    return FileResponse('templates/index.html')

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": exc.errors()})

