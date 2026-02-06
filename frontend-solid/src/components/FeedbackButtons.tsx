// frontend-solid/src/components/FeedbackButtons.tsx

import { Component } from 'solid-js';

interface FeedbackButtonsProps {
  messageId: string;
  onFeedback: (messageId: string, feedbackType: 'positive' | 'negative' | 'partial', comment?: string) => void;
}

export const FeedbackButtons: Component<FeedbackButtonsProps> = (props) => {
  const handleFeedbackClick = (feedbackType: 'positive' | 'negative' | 'partial') => {
    props.onFeedback(props.messageId, feedbackType);
  };

  return (
    <div class="flex items-center space-x-2">
      <button 
        onClick={() => handleFeedbackClick('positive')}
        class="text-green-500 hover:text-green-700"
        title="Gostei da resposta"
      >
        👍
      </button>
      <button 
        onClick={() => handleFeedbackClick('negative')}
        class="text-red-500 hover:text-red-700"
        title="Não gostei da resposta"
      >
        👎
      </button>
      {/* <button 
        onClick={() => handleFeedbackClick('partial')}
        class="text-blue-500 hover:text-blue-700"
        title="Respostas parcialmente útil"
      >
        🤏
      </button> */}
    </div>
  );
};
