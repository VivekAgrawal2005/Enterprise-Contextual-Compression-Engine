from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.documents import router as documents_router
from .api.query import router as query_router
from .api.health import router as health_router

app = FastAPI(title='Enterprise Contextual Compression Engine', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'], allow_origin_regex=r'https://.*\.vercel\.app', allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(health_router, prefix='/api')
app.include_router(documents_router, prefix='/api')
app.include_router(query_router, prefix='/api')

@app.get('/')
def root():
    return {'name': app.title, 'status': 'ok'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('backend.app.main:app', host='0.0.0.0', port=8000, reload=True)

# Run from repository root: uvicorn backend.app.main:app --reload --port 8000
