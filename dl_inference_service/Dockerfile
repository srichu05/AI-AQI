FROM python:3.11-slim

# Create a non-root user with UID 1000 per Hugging Face Spaces security guidelines
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Install dependencies
COPY --chown=user requirements.txt $HOME/app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy service code, custom layer, and model artifact
COPY --chown=user . $HOME/app

# Hugging Face Spaces expects traffic on port 7860
EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
