from spread_eagle.core.database import SessionLocal
from spread_eagle.core.brain import SpreadEagleBrain

def main():
    db = SessionLocal()
    try:
        brain = SpreadEagleBrain(db)
        print("Starting training process for Spread Eagle Brain...")
        brain.train()
        print("Training complete.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
