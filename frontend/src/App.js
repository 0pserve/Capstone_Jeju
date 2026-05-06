import { BrowserRouter, Routes, Route } from "react-router-dom";
import WeatherBar from "./components/WeatherBar";
import SurveyPage from "./pages/SurveyPage";
import MapPage from "./pages/MapPage";

function App() {
  return (
    <BrowserRouter>
      <WeatherBar />
      <Routes>
        <Route path="/"    element={<SurveyPage />} />
        <Route path="/map" element={<MapPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;