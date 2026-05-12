const utcTime = document.querySelector("#utc-time");

function tick() {
  const now = new Date();
  const formatter = new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: "UTC"
  });
  utcTime.textContent = formatter.format(now);
}

tick();
setInterval(tick, 1000);

document.querySelectorAll(".metric strong").forEach((node, index) => {
  node.style.animationDelay = `${index * 45}ms`;
});

const cameraFeed = document.querySelector("#camera-feed");
const cameraStatus = document.querySelector("#camera-status");

function setCameraStatus(label) {
  if (!cameraStatus) {
    return;
  }
  cameraStatus.textContent = label;
}

function connectCameraFeed() {
  if (!cameraFeed) {
    return;
  }

  setCameraStatus("Connecting");
  cameraFeed.onload = () => {
    cameraFeed.dataset.live = "true";
    setCameraStatus("1080p  Live");
  };
  cameraFeed.onerror = () => {
    cameraFeed.dataset.live = "false";
    setCameraStatus("Waiting");
    setTimeout(connectCameraFeed, 1500);
  };
  cameraFeed.src = `/api/camera/stream.mjpg?t=${Date.now()}`;
}

connectCameraFeed();
