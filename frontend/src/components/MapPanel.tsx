import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Polyline, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import type { Stop } from "../types";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

interface MapPanelProps {
  stops: Stop[];
  /** Set only after optimization — no edges until then. */
  routeOrder: number[] | null;
  onAddStop: (stop: Stop) => void;
  focus?: { lat: number; lng: number } | null;
}

function MapFlyTo({ focus }: { focus?: { lat: number; lng: number } | null }) {
  const map = useMap();
  useEffect(() => {
    if (focus) {
      map.flyTo([focus.lat, focus.lng], 14, { duration: 0.8 });
    }
  }, [focus, map]);
  return null;
}

function ClickHandler({ onAddStop }: { onAddStop: (stop: Stop) => void }) {
  useMapEvents({
    click(event) {
      onAddStop({
        lat: event.latlng.lat,
        lng: event.latlng.lng,
        name: "",
      });
    },
  });
  return null;
}

export function MapPanel({ stops, routeOrder, onAddStop, focus }: MapPanelProps) {
  const center: [number, number] = useMemo(() => {
    if (stops.length === 0) return [19.076, 72.8777];
    const lat = stops.reduce((sum, s) => sum + s.lat, 0) / stops.length;
    const lng = stops.reduce((sum, s) => sum + s.lng, 0) / stops.length;
    return [lat, lng];
  }, [stops]);

  const polyline: [number, number][] = useMemo(() => {
    if (!routeOrder || routeOrder.length < 2) return [];
    return routeOrder.map((idx) => [stops[idx].lat, stops[idx].lng] as [number, number]);
  }, [stops, routeOrder]);

  return (
    <MapContainer center={center} zoom={12} className="map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapFlyTo focus={focus} />
      <ClickHandler onAddStop={onAddStop} />
      {stops.map((stop, index) => (
        <Marker key={`${index}-${stop.lat}-${stop.lng}`} position={[stop.lat, stop.lng]} />
      ))}
      {polyline.length >= 2 && (
        <Polyline positions={polyline} pathOptions={{ color: "#2563eb", weight: 4 }} />
      )}
    </MapContainer>
  );
}
