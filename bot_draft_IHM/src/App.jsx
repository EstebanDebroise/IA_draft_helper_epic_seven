import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  return (
    <>
      <div>
        <img src={viteLogo} className="logo" alt="Vite logo" />
        <img src={reactLogo} className="logo react" alt="React logo" />
      </div>
      <h1>Welcome to Draft_bot!</h1>
      <div className="card">
        <div className="menu">
          <button className="button" id="play-button" onClick={handlePlayButtonClick}>
            JOUER
          </button>
          <button className="button" id="settings-button" onClick={handleSettingsButtonClick}>
            PARAMÈTRES
          </button>
          <button className="button" id="quit-button" onClick={handleQuitButtonClick}>
            QUITTER
          </button>
        </div>
      </div>
    </>
  )
}

function handlePlayButtonClick() {
  console.log("Play button clicked");
}

function handleSettingsButtonClick() {
  console.log("Settings button clicked");
}

function handleQuitButtonClick() {
  console.log("Quit button clicked");
}

export default App
