import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Login from './components/ui/Login'
import GitHubConnect from './components/ui/GitHubConnect'
import Navbar from './components/ui/Navbar'

const App = () => (
  <Router>
    <Navbar />
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/github-connect" element={<GitHubConnect />} />
      <Route path="*" element={<Login />} />
    </Routes>
  </Router>
)

export default App
