import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/models.dart';
import '../auth/auth_controller.dart';
import 'chat_controller.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _message = TextEditingController();
  final _scroll = ScrollController();

  @override
  void initState() {
    super.initState();
    Future<void>.microtask(
      () => ref.read(chatControllerProvider.notifier).initialize(),
    );
  }

  @override
  void dispose() {
    _message.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(chatControllerProvider);
    ref.listen(chatControllerProvider, (previous, next) {
      if (next.messages.length != previous?.messages.length) {
        WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToEnd());
      }
    });
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        appBar: AppBar(
          title: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.auto_awesome),
              SizedBox(width: 10),
              Text('MyAgent'),
            ],
          ),
          actions: [
            _ProviderMenu(state: state),
            IconButton(
              tooltip: 'محادثة جديدة',
              onPressed: ref
                  .read(chatControllerProvider.notifier)
                  .newConversation,
              icon: const Icon(Icons.add_comment_outlined),
            ),
          ],
        ),
        drawer: _ConversationDrawer(state: state),
        body: Column(
          children: [
            if (state.error != null)
              MaterialBanner(
                content: const Text('تعذر إكمال الطلب. تحقق من الاتصال.'),
                actions: [
                  TextButton(
                    onPressed: ref
                        .read(chatControllerProvider.notifier)
                        .initialize,
                    child: const Text('إعادة المحاولة'),
                  ),
                ],
              ),
            Expanded(
              child: state.loading
                  ? const Center(child: CircularProgressIndicator())
                  : state.messages.isEmpty
                  ? const _EmptyChat()
                  : ListView.builder(
                      controller: _scroll,
                      padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
                      itemCount: state.messages.length,
                      itemBuilder: (context, index) =>
                          _MessageBubble(message: state.messages[index]),
                    ),
            ),
            _Composer(
              controller: _message,
              sending: state.sending,
              onSend: _send,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _send() async {
    final text = _message.text;
    if (text.trim().isEmpty) return;
    _message.clear();
    await ref.read(chatControllerProvider.notifier).send(text);
  }

  void _scrollToEnd() {
    if (!_scroll.hasClients) return;
    _scroll.animateTo(
      _scroll.position.maxScrollExtent,
      duration: const Duration(milliseconds: 260),
      curve: Curves.easeOut,
    );
  }
}

class _ConversationDrawer extends ConsumerWidget {
  const _ConversationDrawer({required this.state});
  final ChatState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    return Drawer(
      child: SafeArea(
        child: Column(
          children: [
            ListTile(
              leading: const CircleAvatar(child: Icon(Icons.person_outline)),
              title: Text(user?.displayName ?? 'MyAgent User'),
              subtitle: Text(user?.email ?? ''),
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.add),
              title: const Text('محادثة جديدة'),
              onTap: () {
                ref.read(chatControllerProvider.notifier).newConversation();
                Navigator.pop(context);
              },
            ),
            Expanded(
              child: ListView.builder(
                itemCount: state.conversations.length,
                itemBuilder: (context, index) {
                  final item = state.conversations[index];
                  return ListTile(
                    selected: item.id == state.conversationId,
                    leading: const Icon(Icons.chat_bubble_outline),
                    title: Text(
                      item.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete_outline, size: 20),
                      onPressed: () => ref
                          .read(chatControllerProvider.notifier)
                          .deleteConversation(item.id),
                    ),
                    onTap: () {
                      ref
                          .read(chatControllerProvider.notifier)
                          .openConversation(item.id);
                      Navigator.pop(context);
                    },
                  );
                },
              ),
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.logout),
              title: const Text('تسجيل الخروج'),
              onTap: () {
                ref.read(chatControllerProvider.notifier).reset();
                ref.read(authControllerProvider.notifier).logout();
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _ProviderMenu extends ConsumerWidget {
  const _ProviderMenu({required this.state});
  final ChatState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ready = state.providers
        .where((item) => item.configured && item.healthy)
        .toList();
    return PopupMenuButton<String>(
      tooltip: 'نموذج الذكاء',
      icon: const Icon(Icons.hub_outlined),
      initialValue: state.selectedProvider,
      onSelected: ref.read(chatControllerProvider.notifier).selectProvider,
      itemBuilder: (context) => ready
          .map(
            (item) => PopupMenuItem(
              value: item.name,
              child: Text('${item.name} · ${item.model}'),
            ),
          )
          .toList(),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message});
  final ChatMessageModel message;

  @override
  Widget build(BuildContext context) {
    final user = message.role == 'user';
    final colors = Theme.of(context).colorScheme;
    return Align(
      alignment: user ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 680),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(15),
        decoration: BoxDecoration(
          color: user
              ? colors.primaryContainer
              : colors.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SelectableText(message.content),
            if (message.provider != null) ...[
              const SizedBox(height: 8),
              Text(
                message.provider!,
                style: Theme.of(context).textTheme.labelSmall,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.sending,
    required this.onSend,
  });
  final TextEditingController controller;
  final bool sending;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) => SafeArea(
    top: false,
    child: Padding(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              minLines: 1,
              maxLines: 6,
              textInputAction: TextInputAction.newline,
              decoration: const InputDecoration(
                hintText: 'اسأل MyAgent…',
                prefixIcon: Icon(Icons.auto_awesome),
              ),
            ),
          ),
          const SizedBox(width: 8),
          IconButton.filled(
            onPressed: sending ? null : onSend,
            icon: sending
                ? const SizedBox.square(
                    dimension: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.arrow_upward),
          ),
        ],
      ),
    ),
  );
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat();

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.auto_awesome,
            size: 54,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(height: 18),
          Text(
            'كيف أساعدك اليوم؟',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          const Text('ابدأ محادثة؛ الذاكرة والأدوات تعمل من المحرك السحابي.'),
        ],
      ),
    ),
  );
}
