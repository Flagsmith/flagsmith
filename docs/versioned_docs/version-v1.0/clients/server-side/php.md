---
title: Flagsmith PHP SDK
sidebar_label: PHP
description: Manage your Feature Flags and Remote Config in your PHP applications.
slug: /clients/php
---

The SDK client for PHP [https://flagsmith.com/](https://www.flagsmith.com/). Flagsmith allows you to manage feature
flags and remote config across multiple projects, environments and organisations.

The source code for the client is available on [Github](https://github.com/flagsmith/flagsmith-php-client).

## Installation

`composer require flagsmith/flagsmith-php-client`

Requires PHP 7.4 or newer and ships with GuzzleHTTP.

You can optionally provide your own implementation of PSR-18 and PSR-16

> You will also need some implementation of [PSR-18](https://packagist.org/providers/psr/http-client-implementation) and
> [PSR-17](https://packagist.org/providers/psr/http-factory-implementation), for example
> [Guzzle](https://packagist.org/packages/guzzlehttp/guzzle) and
> [PSR-16](https://packagist.org/providers/psr/simple-cache-implementation), for example
> [Symfony Cache](https://packagist.org/packages/symfony/cache). Example:

`composer require flagsmith/flagsmith-php-client guzzlehttp/guzzle symfony/cache`

or

`composer require flagsmith/flagsmith-php-client symfony/http-client nyholm/psr7 symfony/cache`

## Usage

The Flagsmith PHP Client is utilized in such a way that makes it immutable. Every time you change or set a setting the
client will return a clone of itself.

```php
$flagsmith = new Flagsmith('apiToken');
$flagsmithWithCache = $flagsmith->withCache(/** PSR-16 Cache Interface  **/);
```

If you are self hosting an instance of Flagsmith you can set that as the second parameter of the Flagsmith Class, make
sure to include the full path

```php
$flagsmith = new Flagsmith('apiToken', 'https://api.flagsmith.com/api/v1/');
```

### Utilizing Cache

```php
$flagsmith = new Flagsmith('apiToken');
$flagsmithWithCache = $flagsmith
  ->withCache(/** PSR-16 Cache Interface  **/)
  ->withTimeToLive(15); //15 seconds
```

### Get all Flags

Get All feature flags. The flags will be returned as a `Flagsmith\Models\Flag` model

#### Globally

```php
$flagsmith = new \Flagsmith\Flagsmith('apiToken');
$flagsmith->getFlags();
```

#### By Identity

```php
$identity = new \Flagsmith\Models\Identity('identity');

$flagsmith = new \Flagsmith\Flagsmith('apiToken');
$flagsmith->getFlagsByIdentity($identity);
```

### Get Individual Flag

The Individual flag will be returned as a `Flagsmith\Models\Flag` model

#### Get Individual Flag Globally

```php
$flagsmith = new \Flagsmith\Flagsmith('apiToken');
$flagsmith->getFlag('name');
```

#### Get Individual Flag By Identity

```php
$identity = new \Flagsmith\Models\Identity('identity');

$flagsmith = new \Flagsmith\Flagsmith('apiToken');
$flagsmith->getFlagByIdentity($identity, 'name');
```

### Check if Feature is Enabled

Check if a feature is enabled or not

#### Check if Feature is Enabled Globally

```php
$flagsmith = new \Flagsmith\Flagsmith('apiToken');
$flagsmith->isFeatureEnabled('name');
```

#### Check if Feature is Enabled By Identity

```php
$identity = new \Flagsmith\Models\Identity('identity');

$flagsmith = new \Flagsmith\Flagsmith('apiToken');
$flagsmith->isFeatureEnabledByIdentity($identity, 'name');
```

### Get Feature Value

Get the value of a feature

#### Get Feature Value Globally

```php
$flagsmith = new \Flagsmith\Flagsmith('apiToken');
$flagsmith->getFeatureValue('name', 'default value');
```

#### Get Feature Value By Identity

```php
$identity = new \Flagsmith\Models\Identity('identity');

$flagsmith = new \Flagsmith\Flagsmith('apiToken');
$flagsmith->getFeatureValueByIdentity($identity, 'name', 'default value');
```

### Utilizing Identity Traits

You can optionally declare traits against the identity model

```php
$identity = new \Flagsmith\Models\Identity('identity');

$identityTrait = (new \Flagsmith\Models\IdentityTrait('Foo'))->withValue('Bar');

$identity = $identity->withTrait($identityTrait);

$flagsmith = new \Flagsmith\Flagsmith('apiToken');
$flagsmith->getFlagsByIdentity($identity);
```
