import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { useColors } from '@/hooks/useColors';
import { useStarter } from '@/context/StarterContext';

const content: Record<string, { title: string; eyebrow: string; icon: keyof typeof Feather.glyphMap; summary: string; points: string[] }> = {
  navigation: { title: 'Navigation', eyebrow: 'CORE MODULE', icon: 'compass', summary: 'A clear route structure keeps every screen easy to find and easy to extend.', points: ['File-based routes with Expo Router', 'Native tabs with an Android fallback', 'Deep-link friendly screen boundaries'] },
  storage: { title: 'Local storage', eyebrow: 'CORE MODULE', icon: 'database', summary: 'Keep important user choices available even when the device is offline.', points: ['AsyncStorage persistence', 'Small context layer for shared state', 'Resettable preferences with safe defaults'] },
  components: { title: 'UI components', eyebrow: 'CORE MODULE', icon: 'layers', summary: 'A consistent visual language makes new screens feel like part of the same product.', points: ['Semantic light and dark color tokens', 'Reusable pressed, empty and feedback states', 'Accessible touch targets and native patterns'] },
  forms: { title: 'Forms & validation', eyebrow: 'PATTERN', icon: 'edit-3', summary: 'A home for forms that are comfortable to use on a small screen.', points: ['Keyboard-aware layouts', 'Inline validation feedback', 'Clear disabled and loading states'] },
  states: { title: 'Loading & empty states', eyebrow: 'PATTERN', icon: 'loader', summary: 'Good feedback turns waiting and no-data moments into part of the product.', points: ['Meaningful empty copy', 'Retry-ready error surfaces', 'Consistent loading treatment'] },
  networking: { title: 'API-ready networking', eyebrow: 'PATTERN', icon: 'wifi', summary: 'Keep server communication separate so your app can grow without becoming tangled.', points: ['React Query for server state', 'REST-ready client boundary', 'Environment-aware API configuration'] },
  builds: { title: 'Release builds', eyebrow: 'DELIVERY', icon: 'package', summary: 'The project is structured for local development and automated Android builds.', points: ['Versioned app configuration', 'GitHub Actions workflow included', 'APK artifact upload on every build'] },
};

export default function ModuleScreen() {
  const colors = useColors();
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { savedIds, toggleSaved } = useStarter();
  const item = content[id ?? 'navigation'] ?? content.navigation;
  const saved = savedIds.includes(id ?? '');
  const save = async () => { await Haptics.selectionAsync(); toggleSaved(id ?? ''); };

  return (
    <ScrollView style={[styles.screen, { backgroundColor: colors.background }]} contentContainerStyle={{ paddingBottom: insets.bottom + 40 }} showsVerticalScrollIndicator={false}>
      <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
        <Pressable testID="back-button" onPress={() => router.back()} style={({ pressed }) => [styles.back, { backgroundColor: colors.card, borderColor: colors.border, opacity: pressed ? 0.7 : 1 }]}><Feather name="arrow-left" size={20} color={colors.foreground} /></Pressable>
        <Pressable testID="save-button" onPress={save} style={({ pressed }) => [styles.save, { backgroundColor: saved ? colors.accent : colors.card, borderColor: saved ? colors.accent : colors.border, opacity: pressed ? 0.7 : 1 }]}><Feather name={saved ? 'bookmark' : 'bookmark'} size={19} color={saved ? colors.accentForeground : colors.foreground} /></Pressable>
      </View>
      <View style={{ paddingHorizontal: 20 }}>
        <View style={[styles.icon, { backgroundColor: colors.secondary }]}><Feather name={item.icon} size={28} color={colors.primary} /></View>
        <Text style={[styles.eyebrow, { color: colors.primary }]}>{item.eyebrow}</Text>
        <Text style={[styles.title, { color: colors.foreground }]}>{item.title}</Text>
        <Text style={[styles.summary, { color: colors.mutedForeground }]}>{item.summary}</Text>
        <View style={[styles.points, { backgroundColor: colors.card, borderColor: colors.border }]}>
          {item.points.map((point, index) => <View key={point} style={[styles.point, index < item.points.length - 1 && { borderBottomWidth: 1, borderBottomColor: colors.border }]}><View style={[styles.check, { backgroundColor: colors.secondary }]}><Feather name="check" size={14} color={colors.primary} /></View><Text style={[styles.pointText, { color: colors.cardForeground }]}>{point}</Text></View>)}
        </View>
        <View style={[styles.callout, { backgroundColor: colors.secondary }]}><Feather name="info" size={18} color={colors.primary} /><Text style={[styles.calloutText, { color: colors.secondaryForeground }]}>This pattern is ready to customize in your own app.</Text></View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  header: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 20, marginBottom: 35 },
  back: { width: 42, height: 42, borderRadius: 14, borderWidth: 1, justifyContent: 'center', alignItems: 'center' },
  save: { width: 42, height: 42, borderRadius: 14, borderWidth: 1, justifyContent: 'center', alignItems: 'center' },
  icon: { width: 62, height: 62, borderRadius: 20, justifyContent: 'center', alignItems: 'center', marginBottom: 24 },
  eyebrow: { fontFamily: 'Inter_700Bold', fontSize: 11, letterSpacing: 1.4, marginBottom: 9 },
  title: { fontFamily: 'Inter_700Bold', fontSize: 34, lineHeight: 39, letterSpacing: -0.9 },
  summary: { fontFamily: 'Inter_400Regular', fontSize: 15, lineHeight: 23, marginTop: 13, maxWidth: 340 },
  points: { borderRadius: 20, borderWidth: 1, marginTop: 29, paddingHorizontal: 16 },
  point: { flexDirection: 'row', alignItems: 'center', minHeight: 67, gap: 12 },
  check: { width: 30, height: 30, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  pointText: { flex: 1, fontFamily: 'Inter_500Medium', fontSize: 13, lineHeight: 19 },
  callout: { flexDirection: 'row', alignItems: 'center', borderRadius: 17, padding: 15, marginTop: 18, gap: 10 },
  calloutText: { flex: 1, fontFamily: 'Inter_500Medium', fontSize: 12, lineHeight: 18 },
});