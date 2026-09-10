import { useCallback, useMemo, useState } from 'react';
import { FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { useColors } from '@/hooks/useColors';
import { useStarter } from '@/context/StarterContext';

const modules = [
  { id: 'navigation', title: 'Navigation', description: 'Routes, tabs and deep links', icon: 'compass', color: '#0F7F79' },
  { id: 'storage', title: 'Local storage', description: 'Persist app data offline', icon: 'database', color: '#D7813C' },
  { id: 'components', title: 'UI components', description: 'Buttons, cards and states', icon: 'layers', color: '#5B68C4' },
];

export default function HomeScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { savedIds, toggleSaved, ready } = useStarter();
  const [refreshing, setRefreshing] = useState(false);
  const topModules = useMemo(() => modules, []);

  const refresh = useCallback(() => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 500);
  }, []);

  const openModule = async (id: string) => {
    await Haptics.selectionAsync();
    router.push(`/module/${id}`);
  };

  return (
    <View style={[styles.screen, { backgroundColor: colors.background }]}>
      <FlatList
        data={topModules}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingTop: insets.top + 12, paddingBottom: insets.bottom + 96, paddingHorizontal: 20 }}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        ListHeaderComponent={
          <View>
            <View style={styles.topbar}>
              <View>
                <Text style={[styles.eyebrow, { color: colors.primary }]}>ANDROID SOURCE KIT</Text>
                <Text style={[styles.title, { color: colors.foreground }]}>Build from a{'\n'}strong starting point.</Text>
              </View>
              <View style={[styles.avatar, { backgroundColor: colors.secondary }]}>
                <Feather name="code" size={20} color={colors.primary} />
              </View>
            </View>
            <View style={[styles.hero, { backgroundColor: colors.primary }]}>
              <View style={styles.heroCopy}>
                <Text style={styles.heroKicker}>READY TO SHIP</Text>
                <Text style={styles.heroTitle}>Your next Android app starts here.</Text>
                <Text style={styles.heroBody}>A production-ready foundation with the pieces you use most.</Text>
                <View style={styles.heroMeta}>
                  <View style={styles.liveDot} />
                  <Text style={styles.heroMetaText}>v1.0 starter kit</Text>
                </View>
              </View>
              <View style={styles.heroShape}><Feather name="terminal" size={70} color="rgba(255,255,255,0.16)" /></View>
            </View>
            <View style={styles.sectionHeading}>
              <Text style={[styles.sectionTitle, { color: colors.foreground }]}>Included modules</Text>
              <Text style={[styles.sectionCaption, { color: colors.mutedForeground }]}>{ready ? `${savedIds.length} saved` : 'Loading'}</Text>
            </View>
          </View>
        }
        renderItem={({ item, index }) => (
          <Pressable
            testID={`module-${item.id}`}
            onPress={() => openModule(item.id)}
            style={({ pressed }) => [styles.moduleCard, { backgroundColor: colors.card, borderColor: colors.border, opacity: pressed ? 0.82 : 1 }]}
          >
            <View style={[styles.moduleIcon, { backgroundColor: `${item.color}18` }]}>
              <Feather name={item.icon as keyof typeof Feather.glyphMap} size={22} color={item.color} />
            </View>
            <View style={styles.moduleText}>
              <Text style={[styles.moduleTitle, { color: colors.cardForeground }]}>{item.title}</Text>
              <Text style={[styles.moduleDescription, { color: colors.mutedForeground }]}>{item.description}</Text>
            </View>
            <Feather name={savedIds.includes(item.id) ? 'bookmark' : 'chevron-right'} size={20} color={savedIds.includes(item.id) ? colors.accent : colors.mutedForeground} />
          </Pressable>
        )}
        ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
        ListFooterComponent={
          <View style={[styles.footerCard, { backgroundColor: colors.secondary }]}>
            <View style={[styles.footerIcon, { backgroundColor: colors.card }]}><Feather name="github" size={18} color={colors.secondaryForeground} /></View>
            <View style={styles.footerCopy}><Text style={[styles.footerTitle, { color: colors.secondaryForeground }]}>GitHub-ready by default</Text><Text style={[styles.footerBody, { color: colors.mutedForeground }]}>Build locally, push your changes, and automate APK builds.</Text></View>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  topbar: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 22 },
  eyebrow: { fontFamily: 'Inter_700Bold', fontSize: 11, letterSpacing: 1.4, marginBottom: 9 },
  title: { fontFamily: 'Inter_700Bold', fontSize: 31, lineHeight: 36, letterSpacing: -0.8 },
  avatar: { width: 44, height: 44, borderRadius: 15, justifyContent: 'center', alignItems: 'center' },
  hero: { borderRadius: 24, padding: 20, minHeight: 188, overflow: 'hidden', flexDirection: 'row', marginBottom: 28 },
  heroCopy: { flex: 1, zIndex: 1 },
  heroKicker: { color: '#BDECE2', fontFamily: 'Inter_700Bold', fontSize: 10, letterSpacing: 1.2, marginBottom: 12 },
  heroTitle: { color: '#FFFFFF', fontFamily: 'Inter_700Bold', fontSize: 23, lineHeight: 28, letterSpacing: -0.4, maxWidth: 270 },
  heroBody: { color: '#D6F0E9', fontFamily: 'Inter_400Regular', fontSize: 13, lineHeight: 19, marginTop: 10, maxWidth: 260 },
  heroMeta: { flexDirection: 'row', alignItems: 'center', marginTop: 17, gap: 7 },
  liveDot: { width: 7, height: 7, backgroundColor: '#F4B860', borderRadius: 4 },
  heroMetaText: { color: '#E3F5F0', fontFamily: 'Inter_500Medium', fontSize: 11 },
  heroShape: { position: 'absolute', right: 14, bottom: 18, transform: [{ rotate: '-14deg' }] },
  sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 },
  sectionTitle: { fontFamily: 'Inter_700Bold', fontSize: 18, letterSpacing: -0.2 },
  sectionCaption: { fontFamily: 'Inter_500Medium', fontSize: 12 },
  moduleCard: { flexDirection: 'row', alignItems: 'center', padding: 14, borderRadius: 19, borderWidth: 1 },
  moduleIcon: { width: 46, height: 46, borderRadius: 15, justifyContent: 'center', alignItems: 'center' },
  moduleText: { flex: 1, marginLeft: 13 },
  moduleTitle: { fontFamily: 'Inter_600SemiBold', fontSize: 15, marginBottom: 4 },
  moduleDescription: { fontFamily: 'Inter_400Regular', fontSize: 12 },
  footerCard: { flexDirection: 'row', alignItems: 'center', borderRadius: 19, padding: 15, marginTop: 24 },
  footerIcon: { width: 38, height: 38, borderRadius: 13, justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  footerCopy: { flex: 1 },
  footerTitle: { fontFamily: 'Inter_600SemiBold', fontSize: 13, marginBottom: 3 },
  footerBody: { fontFamily: 'Inter_400Regular', fontSize: 11, lineHeight: 16 },
});
