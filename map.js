const source = [50.4501, 30.5234];
const destinations = new Map();
let lastEventId = 0;
let initialized = false;
let skipHiddenEvents = false;
let visibilityVersion = 0;

const map = L.map("map", {
  zoomAnimation: false,
  fadeAnimation: false,
  markerZoomAnimation: false,
  worldCopyJump: false,
}).setView([35, 20], 3);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
  noWrap: true,
}).addTo(map);

L.circleMarker(source, { radius: 6, className: "pulse" })
  .bindTooltip("Источник")
  .addTo(map);

function registerDestination(event) {
  const key = `${event.lat}:${event.lon}`;
  let destination = destinations.get(key);

  if (!destination) {
    destination = {
      marker: L.circleMarker([event.lat, event.lon], {
        radius: 5,
        color: "#00e5ff",
        fillColor: "#00e5ff",
        fillOpacity: 1,
      }).addTo(map),
      count: 0,
      as: event.as || "unknown",
      isp: event.isp || "unknown",
      org: event.org || "unknown",
    };

    destinations.set(key, destination);
  }

  destination.count += 1;
  destination.marker.bindTooltip(
    `Пакетов: ${destination.count}<br>` +
      `AS: ${destination.as}<br>` +
      `ISP: ${destination.isp}<br>` +
      `ORG: ${destination.org}`,
    { direction: "top" },
  );
}

function pointAt(start, end, progress) {
  return [
    start[0] + (end[0] - start[0]) * progress,
    start[1] + (end[1] - start[1]) * progress,
  ];
}

function launchBeam(event) {
  const target = [event.lat, event.lon];
  const beam = L.polyline([source, source], {
    className: "beam",
    opacity: 1,
  }).addTo(map);
  const glow = L.polyline([source, source], {
    className: "beam",
    weight: 9,
    opacity: 0.25,
  }).addTo(map);
  const pulse = L.circleMarker(source, {
    radius: 5,
    className: "pulse",
  }).addTo(map);

  const beamLength = 0.18;
  let progress = 0;

  function animate() {
    const zoomScale = Math.pow(2, map.getZoom() - 3);
    progress += 0.018 / zoomScale;

    const tailProgress = Math.min(progress, 1);
    const headProgress = Math.min(progress + beamLength, 1);
    const tail = pointAt(source, target, tailProgress);
    const head = pointAt(source, target, headProgress);

    beam.setLatLngs([tail, head]);
    glow.setLatLngs([tail, head]);
    pulse.setLatLng(head);

    const opacity =
      progress > 1 ? Math.max(0, 1 - (progress - 1) / beamLength) : 1;

    beam.setStyle({ opacity });
    glow.setStyle({ opacity: opacity * 0.25 });
    pulse.setStyle({ opacity, fillOpacity: opacity });

    if (progress >= 1 + beamLength) {
      map.removeLayer(beam);
      map.removeLayer(glow);
      map.removeLayer(pulse);
      return;
    }

    requestAnimationFrame(animate);
  }

  animate();
}

async function readEvents() {
  if (document.hidden) {
    skipHiddenEvents = true;
    return;
  }

  const requestVisibilityVersion = visibilityVersion;

  try {
    const response = await fetch(`events.json?t=${Date.now()}`);
    if (!response.ok) return;

    if (document.hidden || requestVisibilityVersion !== visibilityVersion) {
      skipHiddenEvents = true;
      return;
    }

    const payload = await response.json();
    const events = Array.isArray(payload) ? payload : [payload];

    if (!initialized) {
      for (const event of events) {
        if (event && event.id > lastEventId) {
          lastEventId = event.id;
        }

        if (event && event.lat != null && event.lon != null) {
          registerDestination(event);
        }
      }

      initialized = true;
      return;
    }

    if (skipHiddenEvents) {
      for (const event of events) {
        if (event && event.id > lastEventId) {
          lastEventId = event.id;
        }
      }

      skipHiddenEvents = false;
      return;
    }

    for (const event of events) {
      if (!event || event.id <= lastEventId) continue;

      lastEventId = Math.max(lastEventId, event.id);
      if (event.lat != null && event.lon != null) {
        registerDestination(event);
        launchBeam(event);
      }
    }
  } catch {
    return;
  }
}

readEvents();
setInterval(readEvents, 300);

document.addEventListener("visibilitychange", () => {
  visibilityVersion += 1;
  skipHiddenEvents = true;

  if (!document.hidden) {
    readEvents();
  }
});
