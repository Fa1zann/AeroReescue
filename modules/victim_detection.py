"""
modules/victim_detection.py
Professional Aerial SAR (Search & Rescue) Engine.
Uses Morphological Top-Hat/Black-Hat Transforms to find high-contrast human anomalies
in both flood waters and earthquake rubble, with tactical UI overlays.
"""

import cv2
import numpy as np
import streamlit as st
import folium

def init_victim_state():
    """Initializes session state for victim tracking."""
    if "victim_detections" not in st.session_state:
        st.session_state["victim_detections"] = []

def nms_filter(boxes, overlap_thresh=0.2):
    """Non-Maximum Suppression to purge overlapping duplicate boxes."""
    if not boxes:
        return []
    boxes_np = np.array(boxes)
    pick = []
    x1 = boxes_np[:, 0]
    y1 = boxes_np[:, 1]
    x2 = boxes_np[:, 0] + boxes_np[:, 2]
    y2 = boxes_np[:, 1] + boxes_np[:, 3]
    scores = boxes_np[:, 4]
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(scores)
    
    while len(idxs) > 0:
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)
        
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])
        
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)
        overlap = (w * h) / area[idxs[:last]]
        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlap_thresh)[0])))
        
    return [boxes[p] for p in pick]

def draw_tactical_bracket(img, x, y, w, h, color=(0, 165, 255)):
    """Draws a professional SAR targeting bracket (corners only + center dot)."""
    t = 2  # Thickness
    l = int(max(w, h) * 0.3)  # Corner length
    l = max(3, l)
    
    # Top-Left
    cv2.line(img, (x, y), (x + l, y), color, t)
    cv2.line(img, (x, y), (x, y + l), color, t)
    # Top-Right
    cv2.line(img, (x + w, y), (x + w - l, y), color, t)
    cv2.line(img, (x + w, y), (x + w, y + l), color, t)
    # Bottom-Left
    cv2.line(img, (x, y + h), (x + l, y + h), color, t)
    cv2.line(img, (x, y + h), (x, y + h - l), color, t)
    # Bottom-Right
    cv2.line(img, (x + w, y + h), (x + w - l, y + h), color, t)
    cv2.line(img, (x + w, y + h), (x + w, y + h - l), color, t)
    # Center precision dot
    cv2.circle(img, (x + w // 2, y + h // 2), 1, (0, 255, 0), -1)

def detect_sar_anomalies(img, sensitivity, target_size):
    """
    Combines Top-Hat and Black-Hat transforms to find small objects (people) 
    that contrast against large backgrounds (water/rubble).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_clahe = clahe.apply(gray)
    
    k_size = int(target_size * 1.5)
    k_size = max(3, k_size if k_size % 2 != 0 else k_size + 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
    
    tophat = cv2.morphologyEx(gray_clahe, cv2.MORPH_TOPHAT, kernel)
    blackhat = cv2.morphologyEx(gray_clahe, cv2.MORPH_BLACKHAT, kernel)
    
    anomalies = cv2.add(tophat, blackhat)
    
    thresh_val = int(255 - (sensitivity * 2.0))
    thresh_val = max(15, min(240, thresh_val))
    _, thresh = cv2.threshold(anomalies, thresh_val, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes = []
    min_area = int(target_size * 0.3)
    max_area = int(target_size * 8.0)
    
    for c in contours:
        area = cv2.contourArea(c)
        if min_area < area < max_area:
            x, y, w, h = cv2.boundingRect(c)
            aspect = float(w) / max(1, h)
            
            if 0.2 <= aspect <= 4.0:
                intensity = np.mean(anomalies[y:y + h, x:x + w])
                conf = round(min(99.5, 60.0 + (intensity / 255.0) * 39.5), 1)
                boxes.append([x, y, w, h, conf])
                
    return nms_filter(boxes, overlap_thresh=0.2)

def analyze_victim_imagery(image_bytes, sector_lat, sector_lon, sector_name, sensitivity=70.0, target_size=20):
    """
    Analyzes drone imagery with target_size and sensitivity tuning parameters.
    """
    init_victim_state()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Could not decode image bytes for victim detection.")

    h, w = img.shape[:2]
    scale = 800.0 / max(h, w)
    resized = cv2.resize(img, (int(w * scale), int(h * scale)))
    
    detected_boxes = detect_sar_anomalies(resized, sensitivity, target_size)
    
    annotated_img = resized.copy()
    new_detections = []
    
    for idx, (x_b, y_b, bw_b, bh_b, conf_score) in enumerate(detected_boxes):
        det_id = f"VICTIM-{len(st.session_state['victim_detections']) + idx + 1:03d}"
        
        draw_tactical_bracket(annotated_img, x_b, y_b, bw_b, bh_b)
        
        label = f"ID:{det_id[-3:]} | {conf_score}%"
        cv2.putText(annotated_img, label, (x_b, max(12, y_b - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 165, 255), 1, cv2.LINE_AA)
        
        lat_offset = (y_b - (resized.shape[0] / 2.0)) * 0.000012
        lon_offset = (x_b - (resized.shape[1] / 2.0)) * 0.000012
        
        new_detections.append({
            "id": det_id,
            "sector": sector_name,
            "confidence": conf_score,
            "status": "UNVERIFIED",
            "lat": sector_lat + lat_offset,
            "lon": sector_lon + lon_offset
        })

    _, buffer = cv2.imencode('.jpg', annotated_img)

    return {
        "annotated_image": buffer.tobytes(),
        "victim_count": len(new_detections),
        "detections": new_detections
    }

def add_victim_layer_to_map(m, victim_detections):
    """Overlays victim detection markers onto the Folium map."""
    if not victim_detections:
        return m

    fg_victims = folium.FeatureGroup(name="🆘 Aerial SAR Detections", show=True)
    for v in victim_detections:
        is_verified = v.get("status") == "VERIFIED"
        icon_color = "green" if is_verified else "orange"
        status_text = "✅ GROUND CONFIRMED" if is_verified else "⚠️ UNVERIFIED (Needs Verification)"
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 220px;">
            <h4 style="margin: 0 0 4px 0; color: {'#10B981' if is_verified else '#F59E0B'};">🆘 {v['id']}</h4>
            <b>Sector:</b> {v['sector']}<br>
            <b>SAR Confidence:</b> {v['confidence']}%<br>
            <b>Status:</b> <br><span style="color: {'#10B981' if is_verified else '#EF4444'}; font-weight: bold;">{status_text}</span>
        </div>
        """
        folium.Marker(
            location=[v['lat'], v['lon']],
            popup=folium.Popup(popup_html, max_width=230),
            tooltip=f"🆘 {v['id']} ({v['confidence']}%) - {v['status']}",
            icon=folium.Icon(color=icon_color, icon="crosshairs", prefix="fa")
        ).add_to(fg_victims)

    fg_victims.add_to(m)
    return m