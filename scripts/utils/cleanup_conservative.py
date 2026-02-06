"""
Script de Limpeza CONSERVADORA do Projeto BI_Solution
Opção 2: Limpa logs, backups, sessões de teste e CSVs temporários

SEGURANÇA:
- Cria backup completo antes de qualquer exclusão
- Mostra preview detalhado
- Pede confirmação antes de executar
- Gera relatório do que foi feito
- Permite reverter (undo)
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import zipfile

class SafeCleanup:
    def __init__(self, root_path):
        self.root = Path(root_path)
        self.backup_dir = self.root / f"BACKUP_LIMPEZA_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'backup_location': str(self.backup_dir),
            'files_to_delete': [],
            'files_deleted': [],
            'errors': [],
            'total_space_freed': 0
        }

        # Padrões de arquivos para EXCLUIR (Opção 2)
        self.patterns_to_delete = {
            'logs': {
                'pattern': '**/*.log',
                'description': 'Arquivos de log temporários',
                'safe': True
            },
            'backups': {
                'pattern': '**/*.backup',
                'description': 'Arquivos de backup (.backup)',
                'safe': True
            },
            'backup_old': {
                'pattern': '**/*_backup_old.py',
                'description': 'Arquivos Python backup antigos',
                'safe': True
            },
            'error_handler_backup': {
                'pattern': '**/error_handler_backup.py',
                'description': 'Backup do error handler',
                'safe': True
            },
            'test_sessions': {
                'pattern': 'backend/app/data/sessions/test-*.json',
                'description': 'Sessões de teste',
                'safe': True
            },
            'cache_test_sessions': {
                'pattern': 'backend/app/data/sessions/cache-test-*.json',
                'description': 'Sessões de cache de teste',
                'safe': True
            },
            'test_cache': {
                'pattern': 'backend/app/data/sessions/test-cache-*.json',
                'description': 'Cache de teste',
                'safe': True
            },
            'test_complex': {
                'pattern': 'backend/app/data/sessions/test-complex.json',
                'description': 'Sessão de teste complexa',
                'safe': True
            },
            'temp_csv': {
                'pattern': 'data/input/*_temp_test.csv',
                'description': 'CSVs temporários de teste',
                'safe': True
            },
            'backend_log_txt': {
                'pattern': 'backend/...backend-log.txt',
                'description': 'Log de backend temporário',
                'safe': True
            },
            # === NOVOS PADRÕES ADICIONADOS EM 28/12/2025 ===
            'obsolete_docs_summary': {
                'pattern': '*_SUMMARY*.md',
                'description': 'Documentação de resumo obsoleta',
                'safe': True
            },
            'obsolete_docs_fix': {
                'pattern': '*_FIX_*.md',
                'description': 'Relatórios de correção obsoletos',
                'safe': True
            },
            'obsolete_docs_async': {
                'pattern': 'ASYNC_RAG_IMPLEMENTATION.md',
                'description': 'Doc RAG Async obsoleta',
                'safe': True
            },
            'obsolete_docs_quickstart': {
                'pattern': 'QUICK_START_MODERNIZATION.md',
                'description': 'Quickstart obsoleto',
                'safe': True
            },
            'backend_docs_obsolete': {
                'pattern': 'backend/*.md',
                'description': 'Docs obsoletas no backend (exceto README/QUICKSTART)',
                'safe': True
            },
            'docs_guides_obsolete': {
                'pattern': 'docs/*_FIX.md',
                'description': 'Guias de correção obsoletos em docs/',
                'safe': True
            },
            'docs_migration_guide': {
                'pattern': 'docs/MIGRATION_GUIDE.md',
                'description': 'Guia de migração (cópia)',
                'safe': True
            },
            'docs_code_chat': {
                'pattern': 'docs/CODE_CHAT_GUIDE.md',
                'description': 'Guia Code Chat',
                'safe': True
            },
            'frontend_docs_obsolete': {
                'pattern': 'frontend-solid/*.md',
                'description': 'Docs obsoletas frontend',
                'safe': True
            },
            'frontend_usage_guide': {
                'pattern': 'frontend-solid/src/migrated-components/USAGE_GUIDE.md',
                'description': 'Guia de uso componentes migrados',
                'safe': True
            },
            'root_tests': {
                'pattern': 'test_*.py',
                'description': 'Scripts de teste na raiz (devem estar em tests/)',
                'safe': True
            },
            'temp_analysis_scripts': {
                'pattern': 'analyze_project*.py',
                'description': 'Scripts temporários de análise',
                'safe': True
            },
            'cleanup_restore_scripts': {
                'pattern': 'restore_backup.py',
                'description': 'Script de restore (protegido manualmente, mas listado para evitar dúvidas)',
                'safe': False # Marcado como False para ser pego pela proteção se tentarem forçar, mas o script protege por nome
            }
        }

        # Diretórios a NUNCA tocar
        self.protected_dirs = {
            'node_modules', '.venv', 'venv', '.git',
            'backend/app/core/agents',
            'backend/app/core/tools',
            'backend/app/infrastructure',
            'frontend-solid/src/pages',
            'frontend-solid/src/components'
        }

        # Arquivos críticos a NUNCA tocar
        self.protected_files = {
            'backend/main.py',
            'backend/requirements.txt',
            'backend/.env',
            'backend/app/data/parquet/admmat.parquet',
            'backend/README.md', # Protegido explicitamente
            'backend/QUICKSTART.md', # Protegido explicitamente
            'package.json',
            'CLAUDE.md',
            'README.md',
            'cleanup_conservative.py', # Auto-proteção
            'cleanup.bat',
            'restore_backup.py',
            'restore.bat',
            'start.bat'
        }

    def is_protected(self, filepath):
        """Verifica se arquivo/diretório está protegido"""
        path_str = str(filepath.relative_to(self.root))

        # Verifica arquivos críticos
        if path_str in self.protected_files:
            return True

        # Verifica diretórios protegidos
        for protected_dir in self.protected_dirs:
            if protected_dir in path_str:
                return True

        # NUNCA tocar em arquivos Python em core/agents ou core/tools (exceto backups)
        if 'backend/app/core/agents' in path_str or 'backend/app/core/tools' in path_str:
            if not any(x in filepath.name for x in ['backup', '_old', '.backup']):
                return True

        # NUNCA tocar em arquivos .parquet
        if filepath.suffix == '.parquet':
            return True

        # NUNCA tocar em cache semântico (apenas logs)
        if 'backend/data/cache/semantic' in path_str and filepath.suffix != '.log':
            return True

        return False

    def find_files_to_delete(self):
        """Encontra arquivos para deletar baseado nos padrões"""
        files_to_delete = []

        for category, config in self.patterns_to_delete.items():
            pattern = config['pattern']
            description = config['description']

            # Busca arquivos pelo padrão
            matches = list(self.root.glob(pattern))

            for filepath in matches:
                # Pula se for diretório
                if filepath.is_dir():
                    continue

                # SEGURANÇA: Verifica se está protegido
                if self.is_protected(filepath):
                    print(f"   PROTEGIDO: {filepath.name} (ignorado)")
                    continue

                # Adiciona à lista
                try:
                    size = filepath.stat().st_size
                    files_to_delete.append({
                        'path': filepath,
                        'relative_path': str(filepath.relative_to(self.root)),
                        'category': category,
                        'description': description,
                        'size': size,
                        'size_formatted': self.format_size(size)
                    })
                except Exception as e:
                    print(f"   ERRO ao processar {filepath}: {e}")

        return files_to_delete

    def format_size(self, size):
        """Formata tamanho em bytes"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    def show_preview(self, files):
        """Mostra preview dos arquivos a serem deletados"""
        print("\n" + "=" * 80)
        print("  PREVIEW - ARQUIVOS QUE SERÃO EXCLUÍDOS")
        print("=" * 80)

        # Agrupa por categoria
        by_category = {}
        total_size = 0

        for file in files:
            category = file['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(file)
            total_size += file['size']

        # Mostra por categoria
        for category, items in sorted(by_category.items()):
            cat_size = sum(f['size'] for f in items)
            print(f"\n[{category.upper()}] {items[0]['description']}")
            print(f"   Total: {len(items)} arquivos ({self.format_size(cat_size)})")

            # Mostra primeiros 5 arquivos
            for file in items[:5]:
                print(f"   - {file['relative_path']} ({file['size_formatted']})")

            if len(items) > 5:
                print(f"   ... e mais {len(items) - 5} arquivos")

        print("\n" + "=" * 80)
        print(f"TOTAL: {len(files)} arquivos | {self.format_size(total_size)} a liberar")
        print("=" * 80)

    def create_backup(self, files):
        """Cria backup dos arquivos antes de deletar"""
        print(f"\nCriando backup em: {self.backup_dir}")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        backup_count = 0
        for file in files:
            try:
                # Cria estrutura de diretórios no backup
                rel_path = file['path'].relative_to(self.root)
                backup_path = self.backup_dir / rel_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)

                # Copia arquivo
                shutil.copy2(file['path'], backup_path)
                backup_count += 1

                if backup_count % 10 == 0:
                    print(f"   Backup: {backup_count}/{len(files)} arquivos...")

            except Exception as e:
                self.report['errors'].append({
                    'file': str(file['path']),
                    'error': f"Erro no backup: {str(e)}"
                })
                print(f"   ERRO ao fazer backup de {file['relative_path']}: {e}")

        print(f"   Backup completo: {backup_count} arquivos salvos")

        # Salva relatório de backup
        backup_report = self.backup_dir / "BACKUP_REPORT.json"
        with open(backup_report, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'files_backed_up': [f['relative_path'] for f in files],
                'total_files': len(files),
                'backup_location': str(self.backup_dir)
            }, f, indent=2, ensure_ascii=False)

        print(f"   Relatório salvo em: {backup_report}")
        return backup_count == len(files)

    def delete_files(self, files):
        """Deleta os arquivos (após backup)"""
        print("\nIniciando exclusão dos arquivos...")

        deleted_count = 0
        total_freed = 0

        for file in files:
            try:
                size = file['size']
                file['path'].unlink()

                self.report['files_deleted'].append(file['relative_path'])
                deleted_count += 1
                total_freed += size

                if deleted_count % 10 == 0:
                    print(f"   Excluídos: {deleted_count}/{len(files)} arquivos...")

            except Exception as e:
                self.report['errors'].append({
                    'file': str(file['path']),
                    'error': f"Erro ao deletar: {str(e)}"
                })
                print(f"   ERRO ao deletar {file['relative_path']}: {e}")

        self.report['total_space_freed'] = total_freed

        print(f"\n   Exclusão completa: {deleted_count} arquivos deletados")
        print(f"   Espaço liberado: {self.format_size(total_freed)}")

        return deleted_count

    def cleanup_empty_dirs(self):
        """Remove diretórios vazios (apenas logs)"""
        print("\nLimpando diretórios vazios...")

        log_dirs = [
            self.root / 'backend' / 'logs',
            self.root / 'logs'
        ]

        removed = 0
        for base_dir in log_dirs:
            if not base_dir.exists():
                continue

            for dirpath, dirnames, filenames in os.walk(base_dir, topdown=False):
                dir_path = Path(dirpath)

                # Só remove se estiver vazio
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        removed += 1
                        print(f"   Removido: {dir_path.relative_to(self.root)}")
                except:
                    pass

        if removed > 0:
            print(f"   {removed} diretórios vazios removidos")
        else:
            print("   Nenhum diretório vazio encontrado")

    def generate_report(self):
        """Gera relatório final"""
        report_file = self.root / f"RELATORIO_LIMPEZA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        # Também gera versão Markdown
        md_file = self.root / f"RELATORIO_LIMPEZA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# Relatório de Limpeza - BI Solution\n\n")
            f.write(f"**Data:** {self.report['timestamp']}\n\n")
            f.write(f"**Backup:** `{self.report['backup_location']}`\n\n")

            f.write("## Resumo\n\n")
            f.write(f"- **Arquivos excluídos:** {len(self.report['files_deleted'])}\n")
            f.write(f"- **Espaço liberado:** {self.format_size(self.report['total_space_freed'])}\n")
            f.write(f"- **Erros:** {len(self.report['errors'])}\n\n")

            f.write("## Arquivos Excluídos\n\n")
            for file in self.report['files_deleted']:
                f.write(f"- `{file}`\n")

            if self.report['errors']:
                f.write("\n## Erros\n\n")
                for error in self.report['errors']:
                    f.write(f"- `{error['file']}`: {error['error']}\n")

            f.write("\n## Como Reverter\n\n")
            f.write("Para reverter a limpeza, execute:\n\n")
            f.write("```bash\n")
            f.write(f"python restore_backup.py \"{self.report['backup_location']}\"\n")
            f.write("```\n")

        print(f"\nRelatórios gerados:")
        print(f"   JSON: {report_file}")
        print(f"   MD:   {md_file}")

        return report_file, md_file

    def run(self, dry_run=False, force=False):
        """Executa a limpeza"""
        print("=" * 80)
        print("  LIMPEZA CONSERVADORA - BI SOLUTION")
        print("  Opção 2: Logs + Backups + Sessões Teste + CSVs Temporários")
        print("=" * 80)

        # 1. Busca arquivos
        print("\n[1/5] Buscando arquivos para excluir...")
        files = self.find_files_to_delete()
        self.report['files_to_delete'] = [f['relative_path'] for f in files]

        if not files:
            print("\nNenhum arquivo encontrado para excluir!")
            return

        # 2. Preview
        self.show_preview(files)

        if dry_run:
            print("\n** MODO DRY-RUN: Nenhum arquivo foi excluído **")
            return

        # 3. Confirmação
        if not force:
            print("\n" + "!" * 80)
            print("  ATENÇÃO: Esta ação irá EXCLUIR os arquivos listados acima!")
            print("  Um backup será criado antes da exclusão.")
            print("!" * 80)

            resposta = input("\nDeseja continuar? Digite 'SIM' para confirmar: ")

            if resposta.strip().upper() != 'SIM':
                print("\nOperação CANCELADA pelo usuário.")
                return
        else:
            print("\nMODO FORCE ATIVADO: Pulando confirmação.")

        # 4. Backup
        print("\n[2/5] Criando backup...")
        if not self.create_backup(files):
            print("\nERRO: Falha ao criar backup. Operação CANCELADA por segurança.")
            return

        # 5. Exclusão
        print("\n[3/5] Excluindo arquivos...")
        deleted = self.delete_files(files)

        # 6. Limpa diretórios vazios
        print("\n[4/5] Limpando diretórios vazios...")
        self.cleanup_empty_dirs()

        # 7. Relatório
        print("\n[5/5] Gerando relatório...")
        self.generate_report()

        # Conclusão
        print("\n" + "=" * 80)
        print("  LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print(f"\n   Arquivos excluídos: {deleted}")
        print(f"   Espaço liberado: {self.format_size(self.report['total_space_freed'])}")
        print(f"   Backup salvo em: {self.backup_dir}")
        print("\n   Para reverter, use o script restore_backup.py")
        print()

if __name__ == "__main__":
    import sys

    # Verifica argumento --dry-run
    dry_run = '--dry-run' in sys.argv or '--preview' in sys.argv
    force = '--force' in sys.argv or '-f' in sys.argv

    cleanup = SafeCleanup(r"C:\Agente_BI\BI_Solution")
    cleanup.run(dry_run=dry_run, force=force)
