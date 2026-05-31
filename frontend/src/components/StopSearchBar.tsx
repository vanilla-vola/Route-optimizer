import { useEffect, useId, useRef, useState } from "react";
import { searchPlaces } from "../api/client";
import type { PlaceSuggestion, Stop } from "../types";

interface StopSearchBarProps {
  onSelectStop: (stop: Stop) => void;
  disabled?: boolean;
}

export function StopSearchBar({ onSelectStop, disabled }: StopSearchBarProps) {
  const listId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PlaceSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setResults([]);
      setLoading(false);
      setSearchError(null);
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      setSearchError(null);
      searchPlaces(trimmed, { signal: controller.signal })
        .then((places) => {
          setResults(places);
          setOpen(true);
          setActiveIndex(-1);
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted) return;
          setResults([]);
          setSearchError(err instanceof Error ? err.message : "Search failed");
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 300);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  const pickSuggestion = (place: PlaceSuggestion) => {
    onSelectStop({ lat: place.lat, lng: place.lng, name: place.name });
    setQuery("");
    setResults([]);
    setOpen(false);
    setActiveIndex(-1);
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || results.length === 0) {
      if (event.key === "Escape") setOpen(false);
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => (i + 1) % results.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => (i <= 0 ? results.length - 1 : i - 1));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      pickSuggestion(results[activeIndex]);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div className="stop-search" ref={rootRef}>
      <label className="stop-search-label" htmlFor={`${listId}-input`}>
        Search for a stop
      </label>
      <input
        id={`${listId}-input`}
        type="search"
        className="stop-search-input"
        placeholder="Address, landmark, city…"
        value={query}
        disabled={disabled}
        autoComplete="off"
        role="combobox"
        aria-expanded={open && results.length > 0}
        aria-controls={`${listId}-listbox`}
        aria-autocomplete="list"
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => {
          if (results.length > 0) setOpen(true);
        }}
        onKeyDown={onKeyDown}
      />
      {loading && <p className="stop-search-hint muted">Searching…</p>}
      {!loading && query.trim().length > 0 && query.trim().length < 2 && (
        <p className="stop-search-hint muted">Type at least 2 characters</p>
      )}
      {searchError && <p className="stop-search-error">{searchError}</p>}
      {open && results.length > 0 && (
        <ul
          id={`${listId}-listbox`}
          className="stop-search-results"
          role="listbox"
        >
          {results.map((place, index) => (
            <li key={`${place.lat}-${place.lng}-${place.name}`}>
              <button
                type="button"
                role="option"
                aria-selected={index === activeIndex}
                className={index === activeIndex ? "active" : undefined}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => pickSuggestion(place)}
              >
                <span className="stop-search-result-name">{place.name}</span>
                {place.subtitle ? (
                  <span className="stop-search-result-sub">{place.subtitle}</span>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
      )}
      {open && !loading && query.trim().length >= 2 && results.length === 0 && !searchError && (
        <p className="stop-search-hint muted">No places found</p>
      )}
    </div>
  );
}
