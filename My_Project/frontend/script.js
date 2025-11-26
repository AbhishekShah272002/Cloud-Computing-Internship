// Replace the apiBase value after you deploy Cloud Run
const apiBase = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API key}";

const cityInput = document.getElementById("city");
document.getElementById("go").onclick = fetchWeather;

let chart = null;
function renderCurrent(data){
  const c = data.current;
  document.getElementById("current").innerHTML = `<b>${c.city}, ${c.country}</b><br/>
    ${c.temp_c} °C, ${c.desc}<br/>Humidity: ${c.humidity}%<br/>Wind: ${c.wind_m_s} m/s`;
}
function renderForecast(data){
  const labels = data.forecast.map(f=>f.dt_txt.split(" ")[0]);
  const temps = data.forecast.map(f=>f.temp_c);
  if(chart) chart.destroy();
  const ctx = document.getElementById("chart").getContext("2d");
  chart = new Chart(ctx, {type:'line', data:{labels, datasets:[{label:'Temp (°C)', data:temps, fill:false}]}, options:{}});
}
function fetchWeather(){
  const city = (cityInput.value||"London").trim();
  document.getElementById("current").innerText = "Loading...";
  fetch(`${apiBase}/getWeather?city=${encodeURIComponent(city)}`)
    .then(r=>r.json()).then(json=>{
      if(json.error){ document.getElementById("current").innerText = "Error: "+json.error; return; }
      renderCurrent(json); renderForecast(json);
    }).catch(e=>{ document.getElementById("current").innerText="Fetch error"; console.error(e); });
}
