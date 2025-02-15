let map, marker, address = "", lat = 0, lng = 0;

window.onload = () => {
    DG.then(() => {
        map = DG.map('map', { center: [55.751244, 37.618423], zoom: 13 });
        marker = DG.marker([55.751244, 37.618423], { draggable: true }).addTo(map);

        marker.on('dragend', async function (e) {
            ({ lat, lng } = e.target.getLatLng());
            try {
                const response = await fetch(`https://catalog.api.2gis.com/3.0/items/geocode?q=${lat},${lng}&key=8e1a3eae-b95b-416a-8f0e-5b69cbcdc23c`);
                const data = await response.json();
                address = data.result?.items[0]?.full_name || "Адрес не найден";
            } catch (error) {
                console.error("Ошибка получения адреса:", error);
                address = "Ошибка определения адреса";
            }
        });
    });

    document.getElementById("confirm").onclick = () => {
        const locationData = { base_position: { address, latitude: lat, longitude: lng } };
        window.Telegram.WebApp.sendData(JSON.stringify(locationData));
        window.Telegram.WebApp.close();
    };
};
