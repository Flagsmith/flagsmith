# Mobile App Development Guide

## Directory Structure

```
mobile/app/
├── components/        # Reusable mobile components
├── screens/          # Screen components
│   └── tabs/        # Tab screen components (Dashboard, Mail, etc.)
├── navigation/       # React Navigation setup
├── styles/          # Mobile-specific styles
└── project/         # Mobile-specific utilities
```

## Key Differences from Web

### 1. Toast Notifications

Mobile uses `react-native-toast-message`, NOT the web toast component.

```typescript
// ✅ Correct for mobile
import Toast from 'react-native-toast-message'

Toast.show({ text1: 'Success message' })
Toast.show({ text1: 'Error message', type: 'error' })

// ❌ Wrong - web only
import { toast } from 'components/base/Toast'
```

### 2. Confirmation Dialogs

Mobile uses native Alert or the `openConfirm` utility (NOT JSX-based modals).

```typescript
// ✅ Correct for mobile
import openConfirm from 'components/utility-components/openConfirm'

openConfirm(
  'Delete Item',
  'Are you sure you want to delete this item?',
  () => handleDelete(),
  undefined, // optional onNo callback
  'Delete',  // optional yes text
  'Cancel'   // optional no text
)

// ❌ Wrong - web only
import { openConfirm } from 'components/base/Modal'
openConfirm('Title', <JSXContent />, callback)
```

### 3. Modals

Mobile uses `CustomModal` component from `components/CustomModal`.

```typescript
// ✅ Correct for mobile
import CustomModal from 'components/CustomModal'

<CustomModal
  isOpen={isOpen}
  onDismiss={onClose}
  title="Modal Title"
>
  <View>{/* content */}</View>
</CustomModal>

// ❌ Wrong - web only
import ModalDefault from 'components/base/ModalDefault'
```

### 4. Icons

Mobile uses the shared `Icon` component from `project/Icon`.

```typescript
// ✅ Correct for mobile
import Icon from 'project/Icon'

<Icon name='edit' fill='primary' />
<Icon name='trash' fill='danger' />
```

### 5. Forms & Inputs

Mobile uses React Native specific form components.

```typescript
// ✅ Correct for mobile
import TextInput from 'components/base/forms/TextInput'
import Button from 'components/base/forms/Button'

<TextInput
  placeholder="Enter text"
  value={value}
  onChangeText={setValue}
  keyboardType="email-address"
  autoCapitalize="none"
/>

<Button onPress={handleSubmit}>Submit</Button>
```

## Component Naming Conventions

Follow these established patterns in `mobile/app/components/`:

### Table Components
- `MailTable.tsx` - Displays mail items
- `TeamTable.tsx` - Displays team members
- `WhatsAppTable.tsx` - Displays WhatsApp numbers with inline edit/delete actions

**WhatsApp Table Pattern:**
The WhatsAppTable component demonstrates the canonical pattern for table/list components with CRUD operations:
- Modal-based create/edit instead of full-screen navigation
- Inline action buttons (Edit/Delete) per row
- Actions hidden for cancelled/inactive items
- Uses `CreateEditNumber` modal for both create and edit modes
- Delete actions use confirmation dialog via `openConfirm`
- State management with `modalOpen` and `editing` for modal control

```typescript
// State management
const [modalOpen, setModalOpen] = useState(false)
const [editing, setEditing] = useState<NumberDetails | null>(null)

// Edit handler - opens modal with data
const handleEdit = (num: NumberDetails) => {
  setEditing(num)
  setModalOpen(true)
}

// Add handler - opens modal without data
const handleAddNew = () => {
  setEditing(null)
  setModalOpen(true)
}

// Modal integration
<CreateEditNumber
  isOpen={modalOpen}
  onClose={() => setModalOpen(false)}
  initial={editing}  // null for create, data for edit
/>
```

### Modal Components
- `CreateEditNumber.tsx` - Create/edit number modal (supports both modes via `initial` prop)
- `RequestDocumentModal.tsx` - Request document modal
- `VerifyAddressChangeModal.tsx` - Address verification modal
- Use `CustomModal` as the base

### Card Components
- `AddressCard.tsx`
- `StatementsCard.tsx`
- `SubscriptionInfoCard.tsx`
- `FeaturedOfferCard.tsx`

### Screen Components
- Located in `mobile/app/screens/tabs/`
- Named with `TabScreen` suffix (e.g., `MailTabScreen.tsx`)
- Export component WITHOUT "Tab" (e.g., `const MailScreen`)
- Export type WITH "Tab" (e.g., `export type MailTabScreen = {}`)

```typescript
// ✅ Correct pattern
export type WhatsAppTabScreen = {}

const WhatsAppScreen: FC<WhatsAppTabScreen & Screen<RootStackParamList>> = () => {
  // ...
}

export default withScreen(WhatsAppScreen)
```

## Styling

### Global Styles Pattern (Preferred)

The mobile app uses a **centralized global styles system** via the `Styles` object, which is automatically available globally (no import needed).

#### When to Use Global Styles (Styles object)

Use global styles for:
- **Spacing** - All margins and padding (mt4, mb3, ph5, p6)
- **Typography** - Text sizes, weights, colors (h1, h4, textBold, textMuted)
- **Colors** - Text and background colors (textPrimary, bgWhite, textDanger)
- **Layout** - Flexbox helpers (flex, row, gap, alignCenter)
- **Common utilities** - list, borderRadius, textCenter

```typescript
// ✅ Correct: Use global styles for common patterns
<View style={[Styles.p4, Styles.mb3]}>
  <Text weight='extraBold' style={Styles.h4}>Title</Text>
  <Text muted style={Styles.mt2}>Description</Text>
</View>

<View style={[Styles.alignCenter, Styles.p6]}>
  <Loader />
</View>

<Row style={Styles.gap}>
  <IconButton icon={<EditIcon />} />
  <IconButton icon={<RemoveIcon />} />
</Row>
```

#### Available Global Style Utilities

**Spacing (based on paddingBase = 4):**
- Margin: m0-m10, mb0-mb10, mt0-mt10, ml0-ml10, mr0-mr10, mh0-mh10, mv0-mv10
- Padding: p0-p10, pb0-pb10, pt0-pt10, pl0-pl10, pr0-pr10, ph0-ph10, pv0-pv10

**Typography:**
- Headings: display, h1, h2, h3, h4, h5
- Weights: textBold, textExtraBold, textSemibold, textLight
- Sizes: textSmall, textExtraSmall
- Alignment: textCenter, textLeft, textRight
- Colors: textMuted, textMutedLight, textPrimary, textDanger, textWhite

**Layout:**
- Flexbox: flex, flexGrow, row, column, gap
- Alignment: alignCenter, alignStart, alignEnd, justifyCenter, justifyStart, justifyEnd
- Containers: container, centeredContainer
- Borders: borderRadius, borderRadiusSm, borderRadiusXs
- Lists: list

**Backgrounds:**
- bgWhite, bgBody, bgPrimary, bgDark
- primary20, primary40, primary60, primary80

### When to Use Local StyleSheet.create

Use local `StyleSheet.create()` **only** for component-specific complex styles:

```typescript
// ✅ Correct: Local styles for component-specific styling
const styles = StyleSheet.create({
  numberCard: {
    backgroundColor: palette.white,
    borderBottomColor: palette.border,
    borderBottomWidth: 1,
    marginBottom: paddingBase,
    padding: paddingBase * 4,
  },
})
```

Use local styles for:
- Complex component-specific styles (shadows, specific borders)
- Detailed layout that won't be reused
- Platform-specific styles (Platform.select())
- Performance-critical styles that shouldn't be recreated

### Common Style Imports (for local styles only)

```typescript
import { StyleSheet } from 'react-native'
import { paddingBase } from 'styles/style_grid'
import { palette } from 'styles/style_variables'

// Note: Styles object is global, no import needed
```

### Hybrid Pattern: Global + Local Styles

```typescript
// ✅ Best practice: Combine global utilities with local component styles
<View style={[Styles.p4, Styles.mb3]}>
  <View style={styles.card}>
    <Text weight='bold' style={Styles.h4}>Title</Text>
    <Text muted style={Styles.mt2}>Description</Text>
  </View>
</View>

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.white,
    borderRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
  },
})
```

## Navigation

### Navigation Architecture

Mobile uses bottom tab navigation with 5 tabs:
1. **Home/Dashboard** (Tab1Container)
2. **Mail** (Tab2Container)
3. **Marketplace** (Tab3Container)
4. **WhatsApp** (Tab4Container)
5. **Settings** (Tab5Container)

**Tab Screens** live in `mobile/app/screens/tabs/` and use:
- `AccountNav` (shows account selector at top)
- `ScreenContainer` wrapper
- Named with `TabScreen` suffix

**Regular Screens** live in `mobile/app/screens/` and use:
- `CustomNavbar` (shows back button)
- No `AccountNav` or `ScreenContainer`
- Accessible from other screens (like Settings menu)

### Tab Screen Pattern

For screens in the bottom tab navigation:

```typescript
// mobile/app/screens/tabs/MailTabScreen.tsx
import { RootStackParamList } from 'navigation/types'
import withScreen, { Screen } from 'screens/withScreen'
import ScreenContainer from 'components/ScreenContainer'
import AccountNav from 'components/AccountNav'

export type MailTabScreen = {}

const MailScreen: FC<MailTabScreen & Screen<RootStackParamList>> = () => {
  return (
    <Flex style={Styles.body}>
      <AccountNav />
      <ScreenContainer withoutNavbar={false}>
        {/* content */}
      </ScreenContainer>
    </Flex>
  )
}

export default withScreen(MailScreen)
```

### Regular Screen Pattern

For screens navigable from other screens (not in tabs):

```typescript
// mobile/app/screens/TeamScreen.tsx
import { RootStackParamList } from 'navigation/types'
import withScreen, { Screen } from 'screens/withScreen'
import CustomNavbar from 'components/CustomNavbar'

export type TeamScreen = {}

const TeamScreen: FC<TeamScreen & Screen<RootStackParamList>> = () => {
  return (
    <View style={Styles.body}>
      <CustomNavbar title='Team'>
        <View>
          {/* content */}
        </View>
      </CustomNavbar>
    </View>
  )
}

export default withScreen(TeamScreen)
```

### Adding a New Screen to Navigation

When adding a new screen, you must update multiple files:

1. **Add route to `route-urls.ts`**:
```typescript
export enum RouteUrls {
  // ...
  'MyNewScreen' = '/my-new-screen',
  // END OF SCREENS
}
```

2. **Add screen import and route to `routes.tsx`**:
```typescript
import MyNewScreen from './screens/MyNewScreen'

export const routes: Record<RouteUrls, IRoute> = {
  // ...
  [RouteUrls.MyNewScreen]: {
    component: MyNewScreen,
    options: {
      headerShown: false,
    },
  },
  // END OF SCREENS
}
```

3. **Add type to `navigation/types.ts`**:
```typescript
import { MyNewScreen } from 'screens/MyNewScreen'

export type RootStackParamList = {
  // ...
  [RouteUrls.MyNewScreen]: MyNewScreen
  // END OF STACKS
}
```

4. **Register in `AppNavigator.tsx`**:
```typescript
<Stack.Screen
  name={RouteUrls.MyNewScreen}
  options={routes[RouteUrls.MyNewScreen].options}
  component={routes[RouteUrls.MyNewScreen].component}
/>
{/* END OF ROUTES*/}
```

### Modifying Tab Navigation

To add or remove bottom tabs, update these files:

1. **`BottomNav.tsx`** - The tab bar UI component:
   - Add/remove `<TabItem>` components
   - Update index numbers for each tab
   - Import necessary icons

2. **`BottomTabsNavigator.tsx`** - Tab navigation logic:
   - Add/remove Stack components (Stack1, Stack2, etc.)
   - Update `<Tab.Screen>` components
   - Update type imports (Tab1StackParamList, etc.)

3. **`route-urls.ts`** - Route definitions:
   - Update TabXContainer routes

4. **`navigation/types.ts`** - Type definitions:
   - Update MainTabParamList
   - Update TabXStackParamList types

**Example: Moving a tab to a regular screen**
```typescript
// 1. Remove from BottomNav.tsx TabItem
// 2. Remove Stack from BottomTabsNavigator.tsx
// 3. Update route-urls.ts to renumber tabs
// 4. Move screen file from screens/tabs/ to screens/
// 5. Change from AccountNav to CustomNavbar in screen
// 6. Add to AppNavigator.tsx Stack.Screen
// 7. Add menu item in Settings or parent screen
```

### Navigation Hooks

```typescript
import { useNavigation } from '@react-navigation/native'
import { NativeStackNavigationProp } from '@react-navigation/native-stack'
import { RootStackParamList } from 'navigation/types'

const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>()

// Navigate to a screen
navigation.push(RouteUrls.MailDetailScreen, { id: '123' })
navigation.navigate(RouteUrls.DashboardScreen)
navigation.goBack()

// From Settings screen, navigate to detail screen
push(RouteUrls.BusinessScreen, {})
```

## Lists & Scrolling

### Use VerticalList for Paginated Data

```typescript
import VerticalList from 'components/VerticalList'
import { useGetMailQuery } from 'common/services/useMail'
import { Req, Res } from 'common/types/requests'

<VerticalList<Req['getMail'], Res['mail']>
  query={useGetMailQuery}
  queryParams={{
    subscription_id: subscriptionId,
    page_size: 20,
  }}
  renderItem={({ item }) => <MailItem mail={item} />}
  ListHeaderComponent={<Header />}
  ListEmptyComponent={<EmptyState />}
  listProps={{
    refreshControl: <RefreshControl />,
  }}
/>
```

### Use FlatList for Simple Lists

```typescript
import { FlatList } from 'react-native'

<FlatList
  data={items}
  renderItem={({ item }) => <Item {...item} />}
  keyExtractor={(item) => item.id}
  ListEmptyComponent={<Text>No items</Text>}
/>
```

## Forms & Screens

### Form Screen Pattern

Use `InviteScreen` as the canonical example for form screens. Key characteristics:

```typescript
import { KeyboardAwareScrollView } from 'react-native-keyboard-controller'
import CustomNavbar from 'components/CustomNavbar'
import Container from 'components/base/grid/Container'
import TextInput from 'components/base/forms/TextInput'
import Button from 'components/base/forms/Button'
import { ErrorMessage } from 'components/Messages'
import withScreen, { Screen } from 'screens/withScreen'

const MyFormScreen: React.FC<MyFormScreen & Screen<RootStackParamList>> = () => {
  const [field, setField] = useState('')
  const isValid = !!field

  const handleSubmit = async () => {
    // Submit logic
    rootPop() // Go back after success
    Toast.show({ text1: 'Success message' })
  }

  return (
    <View style={Styles.body}>
      <CustomNavbar title='Form Title'>
        <KeyboardAwareScrollView>
          <Container>
            <Text style={[Styles.pt5, Styles.pb2]} size='h3'>
              Section Title
            </Text>
            <TextInput
              style={Styles.mb5}
              title='Field Label'
              value={field}
              required
              onChangeText={setField}
            />
            <ErrorMessage>{error}</ErrorMessage>
            <Button
              onPress={handleSubmit}
              style={Styles.mv4}
              disabled={!isValid}
              theme='secondary'
            >
              Submit
            </Button>
          </Container>
        </KeyboardAwareScrollView>
      </CustomNavbar>
    </View>
  )
}
```

**Key Points:**
- Use `KeyboardAwareScrollView` for forms
- Use `CustomNavbar` with back button
- Use `Container` for content padding
- TextInput has `title` prop for labels (NOT separate Text components)
- Add `required` prop to required TextInputs
- Use `rootPop()` to navigate back after success
- Use global `Styles` (no imports needed)

### TextInput Patterns

```typescript
// Basic text input
<TextInput
  style={Styles.mb5}
  title='First Name'
  value={firstName}
  required
  onChangeText={setFirstName}
/>

// Email input with validation
<TextInput
  autoCapitalize='none'
  keyboardType='email-address'
  style={Styles.mb5}
  title='Email Address'
  value={email}
  required
  isValid={isValidEmail(email)}
  onChangeText={setEmail}
/>

// With placeholder
<TextInput
  title='Name'
  placeholder='Give your business number a nickname'
  value={nickname}
  required
  onChangeText={setNickname}
/>
```

### Loading States

```typescript
import Loader from 'components/Loader'

{isLoading && (
  <View style={styles.loaderContainer}>
    <Loader />
  </View>
)}
```

### Empty States

```typescript
{!isLoading && items?.length === 0 && (
  <View style={styles.emptyContainer}>
    <Text style={styles.emptyText}>No items found</Text>
  </View>
)}
```

### Error Handling

```typescript
import { ErrorMessage } from 'components/Messages'

{error && <ErrorMessage>{error}</ErrorMessage>}
```

### Pull to Refresh

```typescript
const [refreshKey, setRefreshKey] = useState()

const refetch = () => {
  setRefreshKey(Date.now())
}

// Pass refreshKey to VerticalList or use RefreshControl
```

## API Integration

Mobile shares the same API services as web from `common/services/`. Follow the API integration guide but use mobile-specific UI patterns for feedback.

### Query Example

```typescript
import { useGetNumbersQuery } from 'common/services/useNumber'

const { data: numbers, isLoading } = useGetNumbersQuery(
  { company_id },
  {
    pollingInterval: 5000, // Poll every 5 seconds
    skip: !company_id,      // Skip if no company_id
  }
)
```

### Mutation Example

```typescript
import { useCreateNumberMutation } from 'common/services/useNumber'
import Toast from 'react-native-toast-message'

const [createNumber, { isLoading }] = useCreateNumberMutation()

const handleSubmit = async () => {
  const result: any = await createNumber(payload)

  if (result.error) {
    Toast.show({ text1: 'Error creating number' })
    return
  }

  Toast.show({ text1: 'Number created successfully' })
}
```

## Testing Mobile Changes

### Run TypeCheck

```bash
npx tsc --noEmit --project mobile/tsconfig.json
```

### Run Linter

```bash
npx eslint mobile/app --fix
```

### Check Staged Files

```bash
npm run check:staged
```

## Handling Cancelled/Inactive Items

When displaying lists that include cancelled or inactive items, follow this pattern:

```typescript
// Visual indicator - reduce opacity for cancelled items
style={[
  styles.numberCard,
  { opacity: num.cancelled_on ? 0.5 : 1 },
]}

// Hide actions for cancelled items
{!num.cancelled_on && (
  <View style={styles.actions}>
    <IconButton onPress={() => handleEdit(num)} icon={<EditIcon />} />
    <IconButton onPress={() => handleDelete(num)} icon={<RemoveIcon />} />
  </View>
)}

// Show cancellation status
{num.cancelled_on && (
  <Text size='small' style={styles.cancelledText}>
    Cancelled on {dateAndTime(num.cancelled_on)}
  </Text>
)}
```

**Key principles:**
- Reduce opacity to 0.5 for visual differentiation
- Hide action buttons completely (not just disable them)
- Show cancellation date/reason if available
- Keep cancelled items visible for historical reference
- Sort cancelled items to the end of the list (handle in API query or transform)

## Common Pitfalls

1. **Don't use web-only imports** in mobile code (like `components/base/Toast`)
2. **Don't use JSX in Alert messages** - use strings only
3. **Always import from path aliases** - never use relative imports
4. **Use `react-native-toast-message`** for toasts, not web toast
5. **Use `openConfirm` utility** for confirms, not web Modal component
6. **Check existing components** before creating new ones - maintain consistency
7. **Don't disable action buttons for cancelled items** - hide them completely instead

## Related Documentation

- See `patterns.md` for general code patterns
- See `api-integration.md` for API service patterns
- See `forms.md` for form validation patterns
