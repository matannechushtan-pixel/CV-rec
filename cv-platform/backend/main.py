from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routers import auth, cv, jobs, applications, roadmap, company, interview, admin, profile

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="CV Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(cv.router, prefix="/cv", tags=["cv"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/applications", tags=["applications"])
app.include_router(roadmap.router, prefix="/roadmap", tags=["roadmap"])
app.include_router(company.router, prefix="/company", tags=["company"])
app.include_router(interview.router, prefix="/interview", tags=["interview"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])


@app.get("/health")
async def health():
    return {"status": "ok"}
