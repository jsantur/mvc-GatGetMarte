
import time
import math
import random

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def benchmark_haversine(iterations=100000):
    start = time.time()
    for _ in range(iterations):
        haversine(-4.58, -81.27, -4.59, -81.28)
    end = time.time()
    return end - start

def benchmark_poi_search(num_units=13, pois_count=60):
    # Simulate searching closest POI for all units
    pois = [{"lat": random.uniform(-4.6, -4.5), "lon": random.uniform(-81.3, -81.2)} for _ in range(pois_count)]
    units = [{"lat": random.uniform(-4.6, -4.5), "lon": random.uniform(-81.3, -81.2)} for _ in range(num_units)]
    
    start = time.time()
    for u in units:
        min_dist = float('inf')
        closest = None
        for p in pois:
            dist = haversine(u['lat'], u['lon'], p['lat'], p['lon'])
            if dist < min_dist:
                min_dist = dist
                closest = p
    end = time.time()
    return end - start

if __name__ == "__main__":
    print(f"--- BENCHMARK RENDIMIENTO PROYECTO ---")
    
    t_hav = benchmark_haversine(100000)
    print(f"100,000 cálculos Haversine: {t_hav:.4f} segundos")
    
    t_poi = benchmark_poi_search(13, 60)
    print(f"Búsqueda POI (13 unidades vs 60 puntos): {t_poi:.6f} segundos")
    
    t_poi_large = benchmark_poi_search(100, 1000)
    print(f"Búsqueda POI escalada (100 unidades vs 1000 puntos): {t_poi_large:.6f} segundos")
