import { Routes, Route, Link } from 'react-router-dom'
import { BarChart3, Trophy, Upload, Cpu, ClipboardList } from 'lucide-react'
import LeaderboardPage from './pages/LeaderboardPage'
import CPUComparisonPage from './pages/CPUComparisonPage'
import SubmitPage from './pages/SubmitPage'
import ResultsPage from './pages/ResultsPage'
import ResultDetailPage from './pages/ResultDetailPage'

function App() {
  return (
    <div className="min-h-screen">
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <BarChart3 className="h-6 w-6 text-blue-600 mr-2" />
              <span className="font-bold text-xl">Video Benchmark</span>
            </div>
            <div className="flex items-center space-x-6">
              <Link to="/" className="flex items-center text-gray-700 hover:text-blue-600">
                <Trophy className="h-4 w-4 mr-1" />
                Leaderboard
              </Link>
              <Link to="/cpus" className="flex items-center text-gray-700 hover:text-blue-600">
                <Cpu className="h-4 w-4 mr-1" />
                CPUs
              </Link>
              <Link to="/results" className="flex items-center text-gray-700 hover:text-blue-600">
                <ClipboardList className="h-4 w-4 mr-1" />
                Results
              </Link>
              <Link to="/submit" className="flex items-center text-gray-700 hover:text-blue-600">
                <Upload className="h-4 w-4 mr-1" />
                Submit
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<LeaderboardPage />} />
          <Route path="/cpus" element={<CPUComparisonPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/result/:id" element={<ResultDetailPage />} />
          <Route path="/submit" element={<SubmitPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
