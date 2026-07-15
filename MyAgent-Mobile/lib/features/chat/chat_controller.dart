import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../shared/models/models.dart';
import 'chat_repository.dart';

class ChatState {
  const ChatState({
    this.conversations = const [],
    this.messages = const [],
    this.providers = const [],
    this.conversationId,
    this.selectedProvider,
    this.loading = false,
    this.sending = false,
    this.error,
  });

  final List<ConversationModel> conversations;
  final List<ChatMessageModel> messages;
  final List<ProviderModel> providers;
  final String? conversationId;
  final String? selectedProvider;
  final bool loading;
  final bool sending;
  final String? error;

  ChatState copyWith({
    List<ConversationModel>? conversations,
    List<ChatMessageModel>? messages,
    List<ProviderModel>? providers,
    String? conversationId,
    String? selectedProvider,
    bool? loading,
    bool? sending,
    String? error,
    bool clearConversation = false,
    bool clearError = false,
  }) =>
      ChatState(
        conversations: conversations ?? this.conversations,
        messages: messages ?? this.messages,
        providers: providers ?? this.providers,
        conversationId:
            clearConversation ? null : conversationId ?? this.conversationId,
        selectedProvider: selectedProvider ?? this.selectedProvider,
        loading: loading ?? this.loading,
        sending: sending ?? this.sending,
        error: clearError ? null : error ?? this.error,
      );
}

class ChatController extends StateNotifier<ChatState> {
  ChatController(this._repository) : super(const ChatState());

  final ChatRepository _repository;
  int _viewRevision = 0;

  Future<void> initialize() async {
    final revision = _viewRevision;
    state = state.copyWith(loading: true, clearError: true);
    try {
      final values = await Future.wait([
        _repository.conversations(),
        _repository.providers(),
      ]);
      final conversations = values[0] as List<ConversationModel>;
      final providers = values[1] as List<ProviderModel>;
      if (revision != _viewRevision) return;
      final ready =
          providers.where((item) => item.configured && item.healthy).toList();
      state = state.copyWith(
        conversations: conversations,
        providers: providers,
        selectedProvider: ready.isEmpty ? 'mock' : ready.first.name,
        loading: false,
      );
    } catch (error) {
      if (revision != _viewRevision) return;
      state = state.copyWith(loading: false, error: error.toString());
    }
  }

  Future<void> openConversation(String id) async {
    final revision = ++_viewRevision;
    state = state.copyWith(conversationId: id, loading: true, clearError: true);
    try {
      final messages = await _repository.messages(id);
      if (revision != _viewRevision || state.conversationId != id) return;
      state = state.copyWith(messages: messages, loading: false);
    } catch (error) {
      if (revision != _viewRevision) return;
      state = state.copyWith(loading: false, error: error.toString());
    }
  }

  void newConversation() {
    _viewRevision += 1;
    state = state.copyWith(
      messages: const [],
      clearConversation: true,
      clearError: true,
    );
  }

  void reset() {
    _viewRevision += 1;
    state = const ChatState();
  }

  void selectProvider(String name) {
    state = state.copyWith(selectedProvider: name);
  }

  Future<void> send(String text) async {
    final message = text.trim();
    if (message.isEmpty || state.sending) return;
    final revision = _viewRevision;
    final optimistic = ChatMessageModel(
      id: 'local_${DateTime.now().microsecondsSinceEpoch}',
      role: 'user',
      content: message,
    );
    state = state.copyWith(
      messages: [...state.messages, optimistic],
      sending: true,
      clearError: true,
    );
    try {
      final reply = await _repository.send(
        message: message,
        conversationId: state.conversationId,
        provider: state.selectedProvider,
      );
      final assistant = ChatMessageModel(
        id: 'local_${DateTime.now().microsecondsSinceEpoch}',
        role: 'assistant',
        content: reply.message,
        provider: reply.provider,
      );
      final conversations = await _repository.conversations();
      if (revision != _viewRevision) {
        return;
      }
      state = state.copyWith(
        conversationId: reply.conversationId,
        messages: [...state.messages, assistant],
        conversations: conversations,
        sending: false,
      );
    } catch (error) {
      if (revision != _viewRevision) return;
      state = state.copyWith(sending: false, error: error.toString());
    }
  }

  Future<void> deleteConversation(String id) async {
    final revision = _viewRevision;
    try {
      await _repository.deleteConversation(id);
      final conversations = await _repository.conversations();
      if (revision != _viewRevision) return;
      final deletingCurrent = state.conversationId == id;
      if (deletingCurrent) _viewRevision += 1;
      state = state.copyWith(
        conversations: conversations,
        messages: deletingCurrent ? const [] : state.messages,
        clearConversation: deletingCurrent,
        clearError: true,
      );
    } catch (error) {
      if (revision != _viewRevision) return;
      state = state.copyWith(error: error.toString());
    }
  }
}

final chatControllerProvider = StateNotifierProvider<ChatController, ChatState>(
  (ref) => ChatController(ref.watch(chatRepositoryProvider)),
);
