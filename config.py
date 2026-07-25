"""Static content and business data for Barbearia BH, Porto.

Business name confirmed as "Barbearia BH" by the client. Note: the three
client-supplied reviews below (see index.html's #reviews section) name
"Barbershop Donk" and barbers "Paulo and Danila" — real customer quotes,
kept verbatim, even though they predate/differ from the confirmed name.

Real service names/prices confirmed by the client (from the shop's actual
price list). `duration_minutes` is still an estimate — not provided by the
client — and `description` is empty for the same reason. `name_en` is the
English label shown when the site's language toggle is set to EN (the
client's price list was transcribed with English translations already);
`name` is the canonical Portuguese label, and is what's sent to the
Google Calendar booking regardless of the customer's language choice, so
the shop owner always sees Portuguese service names on their calendar.

`featured: True` marks the services shown on the front-page marketing
section (a short, curated list — see index.html's #services). The full
list (every service below, featured or not) is shown in the booking flow's
service picker (#page-service's grid), so a customer can always book
anything from there even if it's not teased on the front page.

TODO: "Tintura Global" (full hair coloring) is priced at €5 per the
client's price list, but the transcription tool itself flagged this as
"unusually low and may be incomplete" — every other treatment in this
category costs €5-80, and full hair coloring is normally one of the more
involved/expensive services, not the cheapest. Confirm this price with
the client before launch.
"""

SERVICES = [
    {"id": "simple-haircut", "name": "Corte Simples", "name_en": "Simple Haircut", "description": "", "price": 12, "duration_minutes": 20, "featured": True, "category": "haircuts_beard"},
    {"id": "haircut-beard", "name": "Corte e Barba", "name_en": "Haircut and Beard", "description": "", "price": 20, "duration_minutes": 45, "featured": True, "category": "haircuts_beard"},
    {"id": "fade-haircut", "name": "Corte Degradê", "name_en": "Fade Haircut", "description": "", "price": 15, "duration_minutes": 30, "featured": True, "category": "haircuts_beard"},
    {"id": "beard", "name": "Barba", "name_en": "Beard Trim", "description": "", "price": 8, "duration_minutes": 15, "featured": True, "category": "haircuts_beard"},
    {"id": "eyebrows", "name": "Sobrancelha", "name_en": "Eyebrows", "description": "", "price": 5, "duration_minutes": 10, "featured": True, "category": "grooming"},
    {"id": "blow-dry", "name": "Brush", "name_en": "Blow Dry / Hair Styling", "description": "", "price": 15, "duration_minutes": 30, "featured": True, "category": "grooming"},
    {"id": "hair-sealing", "name": "Selagem", "name_en": "Hair Smoothing / Sealing Treatment", "description": "", "price": 20, "duration_minutes": 60, "featured": False, "category": "haircuts_beard"},
    {"id": "platinum-bleach", "name": "Platina", "name_en": "Platinum Bleach Treatment", "description": "", "price": 50, "duration_minutes": 90, "featured": False, "category": "haircuts_beard"},
    {"id": "highlights", "name": "Madeixas", "name_en": "Highlights", "description": "", "price": 40, "duration_minutes": 90, "featured": False, "category": "haircuts_beard"},
    {"id": "lip-wax", "name": "Buço", "name_en": "Upper Lip Waxing", "description": "", "price": 5, "duration_minutes": 10, "featured": False, "category": "grooming"},
    {"id": "nose-wax", "name": "Cera Nariz", "name_en": "Nose Waxing", "description": "", "price": 5, "duration_minutes": 10, "featured": False, "category": "grooming"},
    {"id": "ear-wax", "name": "Cera Ouvido", "name_en": "Ear Waxing", "description": "", "price": 5, "duration_minutes": 10, "featured": False, "category": "grooming"},
    {"id": "henna-eyebrows", "name": "Sobrancelha Henna", "name_en": "Henna Eyebrows", "description": "", "price": 10, "duration_minutes": 15, "featured": False, "category": "grooming"},
    {"id": "straightening-men", "name": "Alisamento Homem", "name_en": "Men's Hair Straightening", "description": "", "price": 20, "duration_minutes": 60, "featured": False, "category": "hair_treatments"},
    {"id": "straightening-women", "name": "Alisamento Mulher (desde)", "name_en": "Women's Hair Straightening (starting at)", "description": "", "price": 80, "duration_minutes": 120, "featured": False, "category": "hair_treatments"},
    {"id": "facial-cleanse", "name": "Limpeza Facial", "name_en": "Facial Cleansing", "description": "", "price": 5, "duration_minutes": 20, "featured": False, "category": "hair_treatments"},
    {"id": "facial-mask", "name": "Máscara Facial", "name_en": "Facial Mask", "description": "", "price": 5, "duration_minutes": 20, "featured": False, "category": "hair_treatments"},
    {"id": "hair-wash-men", "name": "Lavagem Cabelo Homem", "name_en": "Men's Hair Wash", "description": "", "price": 5, "duration_minutes": 15, "featured": False, "category": "hair_treatments"},
    {"id": "hair-wash-women", "name": "Lavagem Cabelo Mulher", "name_en": "Women's Hair Wash", "description": "", "price": 8, "duration_minutes": 20, "featured": False, "category": "hair_treatments"},
    {"id": "wash-and-blow-dry", "name": "Lavagem + Brush", "name_en": "Hair Wash and Blow Dry", "description": "", "price": 20, "duration_minutes": 45, "featured": False, "category": "hair_treatments"},
    {"id": "hair-hydration", "name": "Hidratação Cabelo", "name_en": "Hair Hydration Treatment", "description": "", "price": 5, "duration_minutes": 20, "featured": False, "category": "hair_treatments"},
    {"id": "body-hair-bleach", "name": "Banho de Lua", "name_en": "Body Hair Bleaching Treatment", "description": "", "price": 10, "duration_minutes": 30, "featured": False, "category": "hair_treatments"},
    # TODO: confirm this price with the client — see module docstring.
    {"id": "full-coloring", "name": "Tintura Global", "name_en": "Full Hair Coloring", "description": "", "price": 5, "duration_minutes": 90, "featured": False, "category": "hair_treatments"},
]

# Confirmed by the client. Monday=0 ... Sunday=6.
BUSINESS_HOURS = {
    0: {"open": "10:00", "close": "20:00"},  # Monday
    1: {"open": "10:00", "close": "20:00"},  # Tuesday
    2: {"open": "10:00", "close": "20:00"},  # Wednesday
    3: {"open": "10:00", "close": "20:00"},  # Thursday
    4: {"open": "10:00", "close": "20:00"},  # Friday
    5: {"open": "09:00", "close": "20:00"},  # Saturday
    6: None,  # Sunday — closed
}

BUSINESS_INFO = {
    "name": "Barbearia BH",
    "address": "Rua de Costa Cabral 82, 4200-129 Porto, Portugal",
    "phone": "+351 925 749 318",
    "instagram": "https://instagram.com/barbeariabhnoporto",
    # WhatsApp assumed to be the same number as `phone` — confirm with the client.
    "whatsapp": "https://wa.me/351925749318",
}
