import { Link, useLocation } from 'react-router-dom'
import './Sidebar.css'
import projectSLogo from '../assets/ProjectS_Logo.png'
import sarawakFlag from '../assets/SarawakFlag.png'

const Sidebar = () => {
  const location = useLocation()

  const navItems = [
    { id: 'home', icon: 'fa-home', label: 'Analytics', path: '/' },
    { id: 'assistant', icon: 'fa-robot', label: 'AI Assistant', path: '/assistant' },
    // { id: 'analytics', icon: 'fa-chart-line', label: 'Analytics' },
    // { id: 'news', icon: 'fa-newspaper', label: 'News' },
    // { id: 'settings', icon: 'fa-cog', label: 'Settings' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-container">
          <img src={projectSLogo} alt="Project S" className="logo-image project-s-logo" />
          <img src={sarawakFlag} alt="Sarawak" className="logo-image sarawak-flag" />
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(item => (
          <Link
            key={item.id}
            to={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <i className={`fas ${item.icon} nav-icon`}></i>
            <span className="nav-label">{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="sidebar-user">
        <div className="user-avatar">
          <i className="fas fa-user"></i>
        </div>
        <span className="user-version">Ver 1.1</span>
      </div>
    </aside>
  )
}

export default Sidebar
