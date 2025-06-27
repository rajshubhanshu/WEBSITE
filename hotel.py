from flask import Flask, render_template_string, request, redirect, session, url_for
import datetime

app = Flask(__name__)
app.secret_key = "secret"

users = {"admin": "admin123"}  # username: password
hotels = [
    {"id": 1, "name": "Hotel Taj", "city": "Mumbai", "price": 5000, "rooms": 5, "rating": 4.5, "amenities": "Pool, Wifi", "reviews": [], "img": "https://images.unsplash.com/photo-1506744038136-46273834b3fb", "desc": "Luxury hotel in Mumbai", "lat": 18.9219841, "lng": 72.8339986},
    {"id": 2, "name": "Hotel Oberoi", "city": "Delhi", "price": 4500, "rooms": 3, "rating": 4.2, "amenities": "Spa, Wifi", "reviews": [], "img": "https://images.unsplash.com/photo-1464983953574-0892a716854b", "desc": "Premium stay in Delhi", "lat": 28.6139391, "lng": 77.2090212},
    {"id": 3, "name": "Hotel Leela", "city": "Bangalore", "price": 4000, "rooms": 2, "rating": 4.0, "amenities": "Gym, Wifi", "reviews": [], "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836", "desc": "Best in Bangalore", "lat": 12.9715987, "lng": 77.5945627},
]
bookings = []

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Hotel Booking</title>
    <style>
        body { font-family: Arial; }
        .hotel { border:1px solid #ccc; margin:10px; padding:10px; display:flex; }
        .hotel img { width:120px; height:80px; object-fit:cover; margin-right:10px; }
        @media (max-width:600px) { .hotel { flex-direction:column; } }
    </style>
</head>
<body>
    {% if session.get('user') %}
        <p>Welcome, {{ session['user'] }} | <a href="{{ url_for('logout') }}">Logout</a>
        {% if session['user']=='admin' %}| <a href="{{ url_for('add_hotel') }}">Add Hotel</a>{% endif %}</p>
    {% else %}
        <a href="{{ url_for('login') }}">Login</a> | <a href="{{ url_for('register') }}">Register</a>
    {% endif %}
    <h1>Hotel List</h1>
    <form method="get">
        Search: <input type="text" name="q" value="{{ request.args.get('q', '') }}">
        <button type="submit">Search</button>
    </form>
    <ul style="list-style:none;padding:0;">
    {% for hotel in hotels %}
        <li class="hotel">
            <img src="{{ hotel.img }}" alt="hotel">
            <div>
                <b>{{ hotel.name }}</b> ({{ hotel.city }}) - ₹{{ hotel.price }}<br>
                Rating: {{ hotel.rating }} | Amenities: {{ hotel.amenities }}<br>
                <a href="{{ url_for('hotel_detail', hotel_id=hotel.id) }}">View / Book</a>
            </div>
        </li>
    {% endfor %}
    </ul>
    {% if session.get('user') %}
        <h2>Your Bookings</h2>
        <ul>
        {% for b in user_bookings %}
            <li>{{ b['hotel'] }} | {{ b['checkin'] }} to {{ b['checkout'] }}</li>
        {% endfor %}
        </ul>
    {% endif %}
</body>
</html>
"""

DETAIL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ hotel.name }}</title>
    <style>
        body { font-family: Arial; }
        img { width:300px; height:200px; object-fit:cover; }
    </style>
</head>
<body>
    <a href="{{ url_for('home') }}">Back to Hotels</a>
    <h1>{{ hotel.name }} ({{ hotel.city }})</h1>
    <img src="{{ hotel.img }}" alt="hotel"><br>
    <p>{{ hotel.desc }}</p>
    <p>Price: ₹{{ hotel.price }} | Rating: {{ hotel.rating }}</p>
    <p>Amenities: {{ hotel.amenities }}</p>
    <p>Rooms Available: {{ hotel.rooms }}</p>
    <p><a href="https://maps.google.com/?q={{ hotel.lat }},{{ hotel.lng }}" target="_blank">View on Map</a></p>
    <h2>Book Now</h2>
    {% if session.get('user') %}
    <form method="post">
        Room Type: <select name="roomtype"><option>Single</option><option>Double</option><option>Suite</option></select><br>
        Check-in: <input type="date" name="checkin" required><br>
        Check-out: <input type="date" name="checkout" required><br>
        <button type="submit">Book</button>
    </form>
    {% else %}
        <p><a href="{{ url_for('login') }}">Login</a> to book</p>
    {% endif %}
    <h2>Reviews</h2>
    <ul>
    {% for r in hotel.reviews %}
        <li>{{ r['user'] }}: {{ r['text'] }} ({{ r['rating'] }}/5)</li>
    {% endfor %}
    </ul>
    {% if session.get('user') %}
    <form method="post" action="{{ url_for('review', hotel_id=hotel.id) }}">
        <input type="text" name="text" placeholder="Write a review" required>
        <select name="rating">
            {% for i in range(1,6) %}
            <option value="{{ i }}">{{ i }}</option>
            {% endfor %}
        </select>
        <button type="submit">Submit Review</button>
    </form>
    {% endif %}
</body>
</html>
"""

LOGIN_HTML = """
<h2>Login</h2>
<form method="post">
    Username: <input name="username" required><br>
    Password: <input name="password" type="password" required><br>
    <button type="submit">Login</button>
</form>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
"""

REGISTER_HTML = """
<h2>Register</h2>
<form method="post">
    Username: <input name="username" required><br>
    Password: <input name="password" type="password" required><br>
    <button type="submit">Register</button>
</form>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
"""

ADD_HOTEL_HTML = """
<h2>Add Hotel (Admin Only)</h2>
<form method="post">
    Name: <input name="name" required><br>
    City: <input name="city" required><br>
    Price: <input name="price" type="number" required><br>
    Rooms: <input name="rooms" type="number" required><br>
    Amenities: <input name="amenities" required><br>
    Description: <input name="desc" required><br>
    Image URL: <input name="img" required><br>
    Latitude: <input name="lat" required><br>
    Longitude: <input name="lng" required><br>
    <button type="submit">Add</button>
</form>
"""

@app.route("/", methods=["GET"])
def home():
    q = request.args.get("q", "").lower()
    filtered = [h for h in hotels if q in h["name"].lower() or q in h["city"].lower()] if q else hotels
    user_bookings = [b for b in bookings if b["user"] == session.get("user")] if session.get("user") else []
    return render_template_string(HTML, hotels=filtered, user_bookings=user_bookings)

@app.route("/hotel/<int:hotel_id>", methods=["GET", "POST"])
def hotel_detail(hotel_id):
    hotel = next((h for h in hotels if h["id"] == hotel_id), None)
    if not hotel:
        return "Hotel not found", 404
    if request.method == "POST" and session.get("user"):
        checkin = request.form["checkin"]
        checkout = request.form["checkout"]
        roomtype = request.form.get("roomtype", "Single")
        # Room availability check (simple)
        if hotel["rooms"] > 0:
            hotel["rooms"] -= 1
            bookings.append({
                "user": session["user"],
                "hotel": hotel["name"],
                "checkin": checkin,
                "checkout": checkout,
                "roomtype": roomtype,
                "date": str(datetime.date.today())
            })
            # Demo: Email confirmation (console print)
            print(f"Email sent to {session['user']} for booking at {hotel['name']}")
            return redirect(url_for("home"))
        else:
            return "No rooms available", 400
    return render_template_string(DETAIL_HTML, hotel=hotel)

@app.route("/hotel/<int:hotel_id>/review", methods=["POST"])
def review(hotel_id):
    hotel = next((h for h in hotels if h["id"] == hotel_id), None)
    if not hotel or not session.get("user"):
        return redirect(url_for("login"))
    text = request.form["text"]
    rating = int(request.form["rating"])
    hotel["reviews"].append({"user": session["user"], "text": text, "rating": rating})
    # Update average rating
    ratings = [r["rating"] for r in hotel["reviews"]]
    hotel["rating"] = round(sum(ratings)/len(ratings), 2)
    return redirect(url_for("hotel_detail", hotel_id=hotel_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        if users.get(u) == p:
            session["user"] = u
            return redirect(url_for("home"))
        else:
            error = "Invalid credentials"
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        if u in users:
            error = "User already exists"
        else:
            users[u] = p
            session["user"] = u
            return redirect(url_for("home"))
    return render_template_string(REGISTER_HTML, error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/add_hotel", methods=["GET", "POST"])
def add_hotel():
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    if request.method == "POST":
        new_id = max(h["id"] for h in hotels) + 1
        hotels.append({
            "id": new_id,
            "name": request.form["name"],
            "city": request.form["city"],
            "price": int(request.form["price"]),
            "rooms": int(request.form["rooms"]),
            "rating": 0,
            "amenities": request.form["amenities"],
            "reviews": [],
            "img": request.form["img"],
            "desc": request.form["desc"],
            "lat": float(request.form["lat"]),
            "lng": float(request.form["lng"])
        })
        return redirect(url_for("home"))
    return render_template_string(ADD_HOTEL_HTML)

if __name__ == "__main__":
    app.run(debug=True)
