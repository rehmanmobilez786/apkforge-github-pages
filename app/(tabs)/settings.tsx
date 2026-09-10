import { Alert, Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useColors } from '@/hooks/useColors';
import { useStarter } from '@/context/StarterContext';

function SettingRow({ icon, title, subtitle, children, onPress }: { icon: keyof typeof Feather.glyphMap; title: string; subtitle: string; children?: React.ReactNode; onPress?: () => void }) {
  const colors = useColors();
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.row, { borderBottomColor: colors.border, opacity: pressed ? 0.7 : 1 }]}>
      <View style={[styles.rowIcon, { backgroundColor: colors.secondary }]}><Feather name={icon} size={18} color={colors.primary} /></View>
      <View style={styles.rowCopy}><Text style={[styles.rowTitle, { color: colors.foreground }]}>{title}</Text><Text style={[styles.rowSubtitle, { color: colors.mutedForeground }]}>{subtitle}</Text></View>
      {children ?? <Feather name="chevron-right" size={18} color={colors.mutedForeground} />}
    </Pressable>
  );
}

export default function SettingsScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { darkMode, setDarkMode, resetPreferences } = useStarter();
  return (
    <ScrollView style={[styles.screen, { backgroundColor: colors.background }]} contentContainerStyle={{ paddingTop: insets.top + 24, paddingBottom: insets.bottom + 96, paddingHorizontal: 20 }} showsVerticalScrollIndicator={false}>
      <Text style={[styles.eyebrow, { color: colors.primary }]}>YOUR FOUNDATION</Text>
      <Text style={[styles.title, { color: colors.foreground }]}>Settings</Text>
      <Text style={[styles.description, { color: colors.mutedForeground }]}>Small choices that stay with your project.</Text>
      <View style={[styles.group, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <SettingRow icon="moon" title="Dark mode" subtitle="Follow your app's visual direction"><Switch testID="dark-mode-switch" value={darkMode} onValueChange={setDarkMode} trackColor={{ false: colors.muted, true: colors.primary }} thumbColor={colors.card} /></SettingRow>
        <SettingRow icon="bookmark" title="Saved modules" subtitle="Keep patterns close while building"><Feather name="check" size={18} color={colors.primary} /></SettingRow>
        <SettingRow icon="refresh-cw" title="Reset preferences" subtitle="Clear saved modules and local choices" onPress={() => Alert.alert('Reset preferences?', 'This will clear your locally saved choices.', [{ text: 'Cancel', style: 'cancel' }, { text: 'Reset', style: 'destructive', onPress: resetPreferences }])} />
      </View>
      <Text style={[styles.groupLabel, { color: colors.mutedForeground }]}>PROJECT INFO</Text>
      <View style={[styles.info, { backgroundColor: colors.secondary }]}>
        <View style={styles.infoLine}><Text style={[styles.infoKey, { color: colors.mutedForeground }]}>Template</Text><Text style={[styles.infoValue, { color: colors.secondaryForeground }]}>Android Source Starter</Text></View>
        <View style={styles.infoLine}><Text style={[styles.infoKey, { color: colors.mutedForeground }]}>Version</Text><Text style={[styles.infoValue, { color: colors.secondaryForeground }]}>1.0.0</Text></View>
        <View style={styles.infoLine}><Text style={[styles.infoKey, { color: colors.mutedForeground }]}>Build</Text><Text style={[styles.infoValue, { color: colors.secondaryForeground }]}>Expo + React Native</Text></View>
      </View>
      <Text style={[styles.tip, { color: colors.mutedForeground }]}>Customize this foundation with your brand, screens, and data layer. The repository is ready for your first commit.</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  eyebrow: { fontFamily: 'Inter_700Bold', fontSize: 11, letterSpacing: 1.4, marginBottom: 9 },
  title: { fontFamily: 'Inter_700Bold', fontSize: 31, lineHeight: 36, letterSpacing: -0.8 },
  description: { fontFamily: 'Inter_400Regular', fontSize: 14, lineHeight: 21, marginTop: 12, marginBottom: 25 },
  group: { borderRadius: 20, borderWidth: 1, paddingHorizontal: 15 },
  row: { minHeight: 77, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1 },
  rowIcon: { width: 38, height: 38, borderRadius: 13, justifyContent: 'center', alignItems: 'center' },
  rowCopy: { flex: 1, marginLeft: 12 },
  rowTitle: { fontFamily: 'Inter_600SemiBold', fontSize: 14, marginBottom: 4 },
  rowSubtitle: { fontFamily: 'Inter_400Regular', fontSize: 11 },
  groupLabel: { fontFamily: 'Inter_700Bold', fontSize: 10, letterSpacing: 1.3, marginTop: 28, marginBottom: 10 },
  info: { padding: 16, borderRadius: 18, gap: 13 },
  infoLine: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  infoKey: { fontFamily: 'Inter_400Regular', fontSize: 12 },
  infoValue: { fontFamily: 'Inter_600SemiBold', fontSize: 12 },
  tip: { fontFamily: 'Inter_400Regular', fontSize: 12, lineHeight: 18, textAlign: 'center', marginTop: 25, paddingHorizontal: 12 },
});