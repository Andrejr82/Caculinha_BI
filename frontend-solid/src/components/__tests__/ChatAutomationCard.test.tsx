import { fireEvent, render, screen } from '@solidjs/testing-library';
import { describe, expect, it, vi } from 'vitest';

import { ChatAutomationCard } from '@/components/ChatAutomationCard';

describe('ChatAutomationCard', () => {
  it('renders approval actions for pending automation', async () => {
    const onApprove = vi.fn();
    const onReject = vi.fn();

    render(() => (
      <ChatAutomationCard
        automation={{
          proposal_id: 'req-1',
          approval_status: 'pending_user_approval',
          action: 'spreadsheet.create_report',
          title: 'Gerar planilha',
          summary: 'Criar planilha exportável sob aprovação explícita.',
        }}
        onApprove={onApprove}
        onReject={onReject}
      />
    ));

    await fireEvent.click(screen.getByRole('button', { name: /aprovar e executar/i }));
    await fireEvent.click(screen.getByRole('button', { name: /rejeitar/i }));

    expect(onApprove).toHaveBeenCalledTimes(1);
    expect(onReject).toHaveBeenCalledTimes(1);
  });
});
