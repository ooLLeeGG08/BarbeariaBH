"""Static content and business data for Barbearia BH, Porto.

Business name confirmed as "Barbearia BH" by the client. Note: the three
client-supplied reviews below (see index.html's #reviews section) name
"Barbershop Donk" and barbers "Paulo and Danila" — real customer quotes,
kept verbatim, even though they predate/differ from the confirmed name.

Real service names/prices confirmed by the client (from the shop's actual
price list). `duration_minutes` is still an estimate — not provided by the
client — and `description` is empty for the same reason.

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
    {"id": "simple-haircut", "name": "Corte Simples", "description": "", "price": 12, "duration_minutes": 20, "featured": True},
    {"id": "haircut-beard", "name": "Corte e Barba", "description": "", "price": 20, "duration_minutes": 45, "featured": True},
    {"id": "fade-haircut", "name": "Corte Degradê", "description": "", "price": 15, "duration_minutes": 30, "featured": True},
    {"id": "beard", "name": "Barba", "description": "", "price": 8, "duration_minutes": 15, "featured": True},
    {"id": "eyebrows", "name": "Sobrancelha", "description": "", "price": 5, "duration_minutes": 10, "featured": True},
    {"id": "blow-dry", "name": "Brush", "description": "", "price": 15, "duration_minutes": 30, "featured": True},
    {"id": "hair-sealing", "name": "Selagem", "description": "", "price": 20, "duration_minutes": 60, "featured": False},
    {"id": "platinum-bleach", "name": "Platina", "description": "", "price": 50, "duration_minutes": 90, "featured": False},
    {"id": "highlights", "name": "Madeixas", "description": "", "price": 40, "duration_minutes": 90, "featured": False},
    {"id": "lip-wax", "name": "Buço", "description": "", "price": 5, "duration_minutes": 10, "featured": False},
    {"id": "nose-wax", "name": "Cera Nariz", "description": "", "price": 5, "duration_minutes": 10, "featured": False},
    {"id": "ear-wax", "name": "Cera Ouvido", "description": "", "price": 5, "duration_minutes": 10, "featured": False},
    {"id": "henna-eyebrows", "name": "Sobrancelha Henna", "description": "", "price": 10, "duration_minutes": 15, "featured": False},
    {"id": "straightening-men", "name": "Alisamento Homem", "description": "", "price": 20, "duration_minutes": 60, "featured": False},
    {"id": "straightening-women", "name": "Alisamento Mulher (desde)", "description": "", "price": 80, "duration_minutes": 120, "featured": False},
    {"id": "facial-cleanse", "name": "Limpeza Facial", "description": "", "price": 5, "duration_minutes": 20, "featured": False},
    {"id": "facial-mask", "name": "Máscara Facial", "description": "", "price": 5, "duration_minutes": 20, "featured": False},
    {"id": "hair-wash-men", "name": "Lavagem Cabelo Homem", "description": "", "price": 5, "duration_minutes": 15, "featured": False},
    {"id": "hair-wash-women", "name": "Lavagem Cabelo Mulher", "description": "", "price": 8, "duration_minutes": 20, "featured": False},
    {"id": "wash-and-blow-dry", "name": "Lavagem + Brush", "description": "", "price": 20, "duration_minutes": 45, "featured": False},
    {"id": "hair-hydration", "name": "Hidratação Cabelo", "description": "", "price": 5, "duration_minutes": 20, "featured": False},
    {"id": "body-hair-bleach", "name": "Banho de Lua", "description": "", "price": 10, "duration_minutes": 30, "featured": False},
    # TODO: confirm this price with the client — see module docstring.
    {"id": "full-coloring", "name": "Tintura Global", "description": "", "price": 5, "duration_minutes": 90, "featured": False},
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
    "phone": "+351 914 520 888",
    "instagram": "https://instagram.com/barbeariabhnoporto",
    # WhatsApp assumed to be the same number as `phone` — confirm with the client.
    "whatsapp": "https://wa.me/351914520888",
}
