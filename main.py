from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
from datetime import timezone
from google.cloud.firestore_v1 import DocumentSnapshot
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from fastapi import Request,FastAPI
from google.auth.transport import requests
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import google.oauth2.id_token
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status
from typing import Optional



cred = credentials.Certificate(r"C:\Users\RajdeepNagar\room-book\firebase_privateKey.json.json")


firebase = firebase_admin.initialize_app(cred)

app = FastAPI()

db = firestore.client()

allow_all = ['*']


app = FastAPI(
    title="Room Booking Application",
    version="1.0.0",
    contact={
        "name": "Nikhil BESOYA",
        "id": "3121452",
        "email": "nikhil.besoya@student.griffith.ie"
    }
)

app.add_middleware(
   CORSMiddleware,
   allow_origins=allow_all,
   allow_credentials=True,
   allow_methods=allow_all,
   allow_headers=allow_all
)


firebase_request_adapter = requests.Request()

app.mount('/static',StaticFiles(directory='static'),name='static')

templates = Jinja2Templates(directory="templates")

@app.get("/",response_class=HTMLResponse)
async def root(request: Request):
    id_token=request.cookies.get("token")
    error_message="No error here"
    user_token = None
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token,firebase_request_adapter)
        except ValueError as err:
            print(str(err))
    return templates.TemplateResponse('main.html',{'request': request,'user_token':user_token,'error_message':error_message})

###############################################



#Room model
class Room(BaseModel):
    room_no: str
    room_type: str
    room_price: float
    username: Optional[str] = None

#Booking model
class Booking(BaseModel):
    room_id: str
    start_time: datetime
    username: Optional[str] = None
    end_time: datetime


# API endpoint to add a new room
@app.post("/rooms/")
async def add_room(room: Room):
    room_ref = db.collection('rooms').document(room.room_no)
    if room_ref.get().exists:
        raise HTTPException(status_code=400, detail="Room already exists")
    room_dict = room.model_dump()
    room_ref.set(room_dict)
    return room_dict

class DeleteRoom(BaseModel):
    room_no: str
    username: Optional[str] = None



# API endpoint to delete a room
@app.delete("/rooms/")
async def delete_room(room: DeleteRoom):
    room_no=room.room_no
    username=room.username
    room_ref = db.collection('rooms').document(room_no)
    room_data = room_ref.get().to_dict()
    if room_data['username'] != username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")
    
    bookings_ref = db.collection('bookings')
    query = bookings_ref.where('room_id', '==', room_no)
    bookings = query.stream()
    if any(bookings):
        raise HTTPException(status_code=400, detail="Room has bookings. Cannot delete.")
    
    room_ref.delete()
    return {"message": "Room deleted successfully"}


#Api endpoint to get all rooms
@app.get("/rooms/", response_model=List[Room])
async def get_all_rooms():
    try:
        rooms_collection = db.collection("rooms").stream()
        rooms = [room.to_dict() for room in rooms_collection]
        return rooms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rooms: {str(e)}")


#api endpoint to add bookings
@app.post("/bookings/")
async def add_booking(booking: Booking):
    room_ref = db.collection('rooms').document(booking.room_id)
    room = room_ref.get()
    if not room.exists:
        raise HTTPException(status_code=404, detail="Room not found")

    # Fetch all bookings for the given room ID
    query = db.collection('bookings').where('room_id', '==', booking.room_id)
    room_bookings = query.stream()

    # Initialize flag to check for overlap
    overlap = False

    # Iterate over each existing booking for the room
    for room_booking in room_bookings:
        room_data: DocumentSnapshot = room_booking
        # Get the start and end times of the existing booking
        existing_start_time = room_data.get('start_time')
        existing_end_time = room_data.get('end_time')
        
        # Check for overlap between existing and new booking
        if (existing_start_time > booking.end_time.replace(tzinfo=timezone.utc)) or (existing_end_time < booking.start_time.replace(tzinfo=timezone.utc)):
            continue
        else:
            overlap=True
            break

    # If overlap is found, raise an exception
    if overlap:
        raise HTTPException(status_code=400, detail="Booking failed : Room is already booked in this time interval")
    else:
        # Add the booking to Firestore
        booking_dict = dict(booking)
        booking_ref=db.collection('bookings').add(booking_dict)
        return {"message": "Booking added successfully"}


#Api endpoint to get all bookings

@app.get("/bookings/")
async def get_bookings():
    try:
        # Reference to the bookings collection
        bookings_ref = db.collection('bookings')
        
        # Query all documents in the bookings collection
        bookings = bookings_ref.stream()
        
        # Initialize an empty list to store booking data
        all_bookings = []
        
        # Iterate over each booking document and extract data
        for booking in bookings:
            booking_data = booking.to_dict()
            all_bookings.append(booking_data)
        return all_bookings
    except Exception as e:
        # If any error occurs, raise an HTTPException with status code 500
        raise HTTPException(status_code=500, detail=f"Error fetching bookings: {e}")
    

# API endpoint to delete a booking
@app.delete("/booking/delete")
async def delete_booking(booking: Booking):
    # Check if the booking exists
    booking_ref = db.collection('bookings').where('room_id', '==', booking.room_id).where('start_time','==',booking.start_time)
    booking_query = booking_ref.stream()
    bookings = list(booking_query)

    # If no booking found, raise HTTPException
    if not bookings:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Since there's only one booking, we can directly access the first element
    booking_doc = bookings[0]
    
    # Check ownership
    if booking_doc.to_dict()['username'] != booking.username:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this booking")

    # Delete the booking
    booking_doc.reference.delete()

    return {"message": "Booking deleted successfully"}


#Api endpoint to get bookings of any particular room for particular day, sorted by time

@app.get("/bookings/{room_no}/{date}",)
async def get_bookings_by_room_and_date(room_no: str, date: str):
    try:
        # Convert the date string to a datetime object
        search_date = datetime.strptime(date, "%Y-%m-%d").date()

        # Get all bookings for the given room ID
        query = db.collection('bookings').where('room_id', '==', room_no).stream()
        all_bookings = [booking.to_dict() for booking in query]

        # Filter bookings that occur on the given date
        bookings_on_date = [booking for booking in all_bookings 
                            if booking['start_time'].date() <= search_date <= booking['end_time'].date()]

        # return bookings_on_date
        sorted_bookings = sorted(bookings_on_date, key=lambda x: x['start_time'])
        return sorted_bookings

    except Exception as e:
        # Handle any errors
        raise HTTPException(status_code=500, detail=f"Error fetching bookings: {e}")



# Run the FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
