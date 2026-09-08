import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./App.css";
import WeatherBar from "./components/WeatherBar";
import SurveyPage from "./pages/SurveyPage";
import MapPage from "./pages/MapPage";
import PlansPage from "./pages/PlansPage";

function App() {
  return (
    <BrowserRouter>
      <WeatherBar />
      <Routes>
        <Route path="/"    element={<SurveyPage />} />
        <Route path="/plans" element={<PlansPage />} />
        <Route path="/map" element={<MapPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
