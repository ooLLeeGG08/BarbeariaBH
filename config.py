"""Static content and business data for Barbearia BH, Porto.

Business name confirmed as "Barbearia BH" by the client. Note: the three
client-supplied reviews below (see index.html's #reviews section) name
"Barbershop Donk" and barbers "Paulo and Danila" — real customer quotes,
kept verbatim, even though they predate/differ from the confirmed name.

TODO: service descriptions and durations are placeholders: the service
list itself (names and prices) was confirmed by the client as "same as
noble website for now", but noble's site only ever had names and prices —
no descriptions or durations — so those two fields are estimates pending
real client input.
"""

SERVICES = [
    {"id": "classic-haircut", "name": "Corte clássico", "description": "", "price": 12, "duration_minutes": 30},
    {"id": "clipper-haircut", "name": "Corte máquina", "description": "", "price": 10, "duration_minutes": 20},
    {"id": "fade-haircut", "name": "Corte degradê", "description": "", "price": 14, "duration_minutes": 30},
    {"id": "haircut-beard", "name": "Corte e barba", "description": "", "price": 20, "duration_minutes": 45},
    {"id": "beard", "name": "Barba", "description": "", "price": 7, "duration_minutes": 15},
    {"id": "premium-beard", "name": "Barba premium", "description": "", "price": 10, "duration_minutes": 20},
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
