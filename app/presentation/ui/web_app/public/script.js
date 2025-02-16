let map, marker;
const defaultLat = 59.94028, defaultLng = 30.369012;  

window.onload = () => {
    DG.then(() => {
        let storedLat = localStorage.getItem("latitude");
        let storedLng = localStorage.getItem("longitude");

        let lat = defaultLat;
        let lng = defaultLng;

        map = DG.map("map", { center: [lat, lng], zoom: 13 });

        marker = DG.marker([lat, lng]).addTo(map);

        map.on('click', (e) => {
            let { lat, lng } = e.latlng;
            marker.setLatLng([lat, lng]);
            localStorage.setItem("latitude", lat);
            localStorage.setItem("longitude", lng);
            console.log("Выбранные координаты:", lat, lng);
        });
    });
};

document.getElementById("confirm").onclick = () => {
    let lat = localStorage.getItem("latitude");
    let lng = localStorage.getItem("longitude");

    if (!lat || !lng) {
        window.Telegram.WebApp.showAlert("❌ Ошибка: выберите точку на карте!");
        return;
    }

    sendLocationData(lat, lng, true);
};

function sendLocationData(lat, lng, closeWebApp = false) {
    const locationData = JSON.stringify({ latitude: lat, longitude: lng });

    window.Telegram.WebApp.sendData(locationData);

    if (closeWebApp) {
        window.Telegram.WebApp.showAlert(locationData, () => {
            setTimeout(() => window.Telegram.WebApp.close(), 100);
        });
    }
}
