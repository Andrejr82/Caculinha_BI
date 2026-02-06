import { Component } from 'solid-js';
import './TypingIndicator.css';

export const TypingIndicator: Component = () => {
  return (
    <div class="typing-indicator">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
  );
};
