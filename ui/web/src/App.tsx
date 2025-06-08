import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Login from './components/ui/Login'
import GitHubConnect from './components/ui/GitHubConnect'
import Navbar from './components/ui/Navbar'
import GithubCallback from './components/ui/GithubCallback'
import Home from './components/ui/Home'
import TrackingPlan from './components/ui/TrackingPlan'

const App = () => (
  <Router>
    <Navbar />
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/github-connect" element={<GitHubConnect />} />
      <Route path="/github-callback" element={<GithubCallback />} />
      <Route path="/home" element={<Home />} />
      <Route path="/tracking-plan" element={<TrackingPlan />} />
      <Route path="*" element={<Login />} />
    </Routes>
  </Router>
)

export default App
