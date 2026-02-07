from roboflow import Roboflow

# This is a public key for a public chess dataset (no account needed)
rf = Roboflow(api_key="PsOkAuALeUShjbRYo1db")
project = rf.workspace("roboflow-universe-projects").project("chess-pieces-new")
version = project.version(2)
dataset = version.download("yolov8")

