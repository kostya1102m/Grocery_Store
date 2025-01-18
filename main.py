from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers.product import router as product
from routers.user import router as user
from routers.order import router as order

app = FastAPI()

app.include_router(product)

app.include_router(user)

app.include_router(order)

origins = [
    "http://127.0.0.1:8075",
    "http://127.0.0.1:8076"
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
