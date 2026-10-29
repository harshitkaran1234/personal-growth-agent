import uvicorn

if __name__ == "__main__":
    uvicorn.run("personal_growth_agent.main:app", host="0.0.0.0", port=8000, reload=True)
