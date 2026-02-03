import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js'
import { Bar, Doughnut } from 'react-chartjs-2'
import './Charts.css'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement)

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

export function Charts({ summary, data }) {
  const typeDist = summary?.type_distribution || {}
  const averages = summary?.averages || {}
  const avgLabels = Object.keys(averages).filter((k) => averages[k] != null)
  const avgValues = avgLabels.map((k) => averages[k])

  const barData = {
    labels: avgLabels,
    datasets: [
      {
        label: 'Average',
        data: avgValues,
        backgroundColor: CHART_COLORS.slice(0, avgLabels.length),
      },
    ],
  }

  const doughnutData = {
    labels: Object.keys(typeDist),
    datasets: [
      {
        data: Object.values(typeDist),
        backgroundColor: CHART_COLORS,
        borderWidth: 0,
      },
    ],
  }

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: { display: true, text: 'Averages (Flowrate, Pressure, Temperature)' },
    },
    scales: {
      y: { beginAtZero: true, grid: { color: 'rgba(148,163,184,0.15)' }, ticks: { color: '#94a3b8' } },
      x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
    },
  }

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'right', labels: { color: '#e2e8f0', padding: 12 } },
      title: { display: true, text: 'Equipment type distribution' },
    },
  }

  return (
    <section className="charts-section">
      <div className="chart-box">
        {avgLabels.length > 0 && (
          <div className="chart-container bar-chart">
            <Bar data={barData} options={barOptions} />
          </div>
        )}
      </div>
      <div className="chart-box">
        {Object.keys(typeDist).length > 0 && (
          <div className="chart-container doughnut-chart">
            <Doughnut data={doughnutData} options={doughnutOptions} />
          </div>
        )}
      </div>
    </section>
  )
}
