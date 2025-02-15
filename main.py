from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User, Contact, Message
from auth import *
import models
from schemas import MessageCreate, UserCreate, UserLogin

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication
@app.post("/signup")
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@app.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Token creation in auth.py
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Contacts
@app.post("/contacts/add")
async def add_contact(
    contact_username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contact = db.query(User).filter(User.username == contact_username).first()
    if not contact:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_contact = db.query(Contact).filter(
        (Contact.user_id == current_user.id) & 
        (Contact.contact_id == contact.id)
    ).first()
    
    if existing_contact:
        raise HTTPException(status_code=400, detail="Contact already added")
    
    new_contact = Contact(user_id=current_user.id, contact_id=contact.id)
    db.add(new_contact)
    db.commit()
    return {"message": "Contact added successfully"}

# Messages
@app.post("/messages/send")
async def send_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    receiver = db.query(User).filter(User.username == message.receiver_username).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    new_message = Message(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=message.content
    )
    db.add(new_message)
    db.commit()
    return {"message": "Message sent successfully"}

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/chat")
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


# Get current user
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "about": current_user.about,
        "profile_picture": current_user.profile_picture
    }

# Get contacts
@app.get("/contacts")
async def get_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contacts = db.query(Contact).filter(Contact.user_id == current_user.id).all()
    return [
        {
            "id": contact.contact_id,
            "username": db.query(User).get(contact.contact_id).username,
            "lastMessage": "..." 
        }
        for contact in contacts
    ]

# Get messages
@app.get("/messages/{contact_id}")
async def get_messages(contact_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == contact_id)) |
        ((Message.sender_id == contact_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()
    
    return [
        {
            "id": msg.id,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "sender_id": msg.sender_id
        }
        for msg in messages
    ]