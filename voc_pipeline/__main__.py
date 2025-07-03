import fire
from .processor import process_transcript

if __name__ == "__main__":
    fire.Fire({
        # expose only the new function
        "process_transcript": process_transcript,
    }) 