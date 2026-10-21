export class ApiError extends Error {
  public status: number;
  public details?: unknown;

  constructor(status: number, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, string | number | boolean | null | undefined>;
}

export class HttpClient {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL ?? "") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/+$/, "");
  }

  private getToken(): string | null {
    if (typeof window !== "undefined" && window.localStorage) {
      return window.localStorage.getItem("auth_token");
    }
    return null;
  }

  private handleUnauthorized(): void {
    if (typeof window !== "undefined" && window.localStorage) {
      window.localStorage.removeItem("auth_token");
      window.localStorage.removeItem("auth_user");
      if (window.location && window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
  }

  private buildUrl(path: string, params?: Record<string, string | number | boolean | null | undefined>): string {
    const isAbsolute = path.startsWith("http://") || path.startsWith("https://");
    const cleanPath = isAbsolute
      ? path
      : this.baseUrl
      ? `${this.baseUrl}/${path.replace(/^\/+/, "")}`
      : `/${path.replace(/^\/+/, "")}`;

    if (!params) {
      return cleanPath;
    }

    // Supply window.location.origin in browser, or fallback base for server/test environments
    const baseOrigin =
      typeof window !== "undefined" && window.location?.origin
        ? window.location.origin
        : "http://127.0.0.1:8080";

    const url = new URL(cleanPath, baseOrigin);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        url.searchParams.append(key, String(value));
      }
    });

    // If original path was relative, preserve relative pathname + search
    if (!isAbsolute && !this.baseUrl) {
      return `${url.pathname}${url.search}`;
    }

    return url.toString();
  }

  public async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { params, body, headers: customHeaders, ...customOptions } = options;
    const url = this.buildUrl(path, params);

    const headers: Record<string, string> = {
      Accept: "application/json",
      ...(customHeaders as Record<string, string>),
    };

    const token = this.getToken();
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    let requestBody: BodyInit | undefined;
    if (body !== undefined && body !== null) {
      if (typeof body === "string" || body instanceof FormData || body instanceof URLSearchParams) {
        requestBody = body;
      } else {
        headers["Content-Type"] = "application/json";
        requestBody = JSON.stringify(body);
      }
    }

    let response: Response;
    try {
      response = await fetch(url, {
        ...customOptions,
        headers,
        body: requestBody,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Network error";
      throw new ApiError(0, `Network error communicating with backend: ${msg}`);
    }

    if (response.status === 401) {
      this.handleUnauthorized();
      throw new ApiError(401, "Unauthorized - token expired or invalid");
    }

    if (!response.ok) {
      const rawText = await response.text()
      let errorData: unknown;
      try {
        errorData = JSON.parse(rawText)
      } catch {
        errorData = rawText
      }

      let message = `Request failed with status ${response.status}`;
      if (typeof errorData === "object" && errorData !== null) {
        const errorObj = errorData as Record<string, unknown>;
        if (typeof errorObj.detail === "string") {
          message = errorObj.detail;
        } else if (Array.isArray(errorObj.detail)) {
          message = errorObj.detail.map((e) => (typeof e === "object" && e?.msg ? e.msg : JSON.stringify(e))).join(", ");
        } else if (typeof errorObj.message === "string") {
          message = errorObj.message;
        }
      }
      throw new ApiError(response.status, message, errorData);
    }

    if (response.status === 204) {
      return undefined as unknown as T;
    }

    try {
      return (await response.json()) as T;
    } catch {
      return (await response.text()) as unknown as T;
    }
  }

  public get<T>(path: string, options: Omit<RequestOptions, "body"> = {}): Promise<T> {
    return this.request<T>(path, { ...options, method: "GET" });
  }

  public post<T>(path: string, body?: unknown, options: Omit<RequestOptions, "body"> = {}): Promise<T> {
    return this.request<T>(path, { ...options, method: "POST", body });
  }

  public put<T>(path: string, body?: unknown, options: Omit<RequestOptions, "body"> = {}): Promise<T> {
    return this.request<T>(path, { ...options, method: "PUT", body });
  }

  public patch<T>(path: string, body?: unknown, options: Omit<RequestOptions, "body"> = {}): Promise<T> {
    return this.request<T>(path, { ...options, method: "PATCH", body });
  }

  public delete<T>(path: string, options: Omit<RequestOptions, "body"> = {}): Promise<T> {
    return this.request<T>(path, { ...options, method: "DELETE" });
  }
}

export const httpClient = new HttpClient();
